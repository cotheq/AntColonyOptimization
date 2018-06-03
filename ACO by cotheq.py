import pygame as pg
import math as m
import random as r

# цветовые константы
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (100, 100, 0)
TEAL = (0, 80, 80)

# масштаб графического окна
scale = 6

numAnts = 1000 # общее кол-во муравьев
leetQ = 5 # процент элитных муравьев
initFeromone = 1.0 # начальное значение феромона

# кол-во еды
foodList = []
numFood = 30 # количество еды
minFoodDistance = 20 #минимальное расстояние до еды по каждой стороне
maxFoodDistance = 100 #максимальное расстояние до еды по каждой стороне
foodAmounts = []
initialFoodAmount = 50 # начальное количество еды

# кол-во препятствий
numObstacles = 4000
freeSpace = 3 #свободное пространство, оставляемое вокруг спавна и еды

# параметры алгоритма
alpha = 3 # степень количества феромона (влияет на вероятность пойти туда, где его больше)
beta = 3 # степень величины, обратной расстоянию (в данном случае, влияет на приоритет ходов по прямой)
q = 100 # множитель на величину обратную пройденному пути (кол-во оставляемого феромона)
p = 0.0003 # локальный коэффицицент испарения
gp = 0.0007 # глобальный коэффицицент испарения

# инициализация
pg.init()
pg.display.set_caption("Муравьиный алгоритм")
screen = pg.display.set_mode([int(100 * scale), int(100 * scale)])
clock = pg.time.Clock()
ants = []
matrix = []
spawnX, spawnY = 0, 0
iterations = 0

enableDrawAnts = True # вкл/выкл отрисовку муравьев
enableMessages = True # вкл/выкл сообщения в консоли
enableLostMessage = False

#класс Муравей
class Ant:
	global spawnX
	global spawnY
	def __init__(self, x, y, leet):
		self.x = x
		self.y = y
		self.tabooList = []
		self.putFeromone = False
		self.l0 = 0
		self.tabooListIndex = 0
		self.leet = leet
		self.id = r.randint(10000000, 99999999)
	# dir - направление. 0 <= dir <= 7
	# 0 - вверх, далее как по часовой стрелке
	def move(self, dir):
		if [self.x, self.y] not in self.tabooList:
			self.tabooList.append([self.x, self.y])
		dx, dy = 0, 0
			
		if dir == 0:
			dy = -1
		if dir == 1:
			dy = -1
			dx = 1
		if dir == 2:
			dx = 1
		if dir == 3:
			dx = 1
			dy = 1
		if dir == 4:
			dy = 1
		if dir == 5:
			dy = 1
			dx = -1
		if dir == 6:
			dx = -1
		if dir == 7:
			dx = -1
			dy = -1

		self.x += dx
		self.y += dy
		
		if [self.x, self.y] not in self.tabooList:
			self.tabooList.append([self.x, self.y])

		if (dx * dy == 0):
			self.l0 += 1
		else:
			self.l0 += 2 ** .5

	def tryMove(self, dir):
		if dir == 0:
			return [self.x, self.y - 1]
		if dir == 1:
			return [self.x + 1, self.y - 1]
		if dir == 2:
			return [self.x + 1, self.y]
		if dir == 3:
			return [self.x + 1, self.y + 1]
		if dir == 4:
			return [self.x, self.y + 1]
		if dir == 5:
			return [self.x - 1, self.y + 1]
		if dir == 6:
			return [self.x - 1, self.y]
		if dir == 7:
			return [self.x - 1, self.y - 1]

	# узнаём кол-во феромона на соседних клетках
	def getFeromone(self, dir):
		feromoneX = self.x
		feromoneY = self.y
		if dir == 0:
			feromoneY = self.y - 1
		if dir == 1:
			feromoneY = self.y - 1
			feromoneX = self.x + 1
		if dir == 2:
			feromoneX = self.x + 1
		if dir == 3:
			feromoneX = self.x + 1
			feromoneY = self.y + 1
		if dir == 4:
			feromoneY = self.y + 1
		if dir == 5:
			feromoneY = self.y + 1
			feromoneX = self.x - 1
		if dir == 6:
			feromoneX = self.x - 1
		if dir == 7:
			feromoneX = self.x - 1
			feromoneY = self.y - 1

		if type(matrix[feromoneX][feromoneY]) == type(0.0):			
			return matrix[feromoneX][feromoneY]
		else:
			return initFeromone * 10000

	# функция возвращает величину, обратную расстоянию
	def getInverseDistance(self, dir):
		if (dir == 0) or (dir == 2) or (dir == 4) or (dir == 6):
			return 1.0 # по прямой расстояние равно 1
		else:
			return float(1 / 2 ** .5) # по диагонали расстояние равно корню из 2

	#определяем возможные ходы (проверка на наличие в табу листе)
	possibleTurns = []	
	def addPossibleTurns(self, arr):
		self.possibleTurns = []
		for i in arr:
			pp = self.tryMove(i)
			if not(pp in self.tabooList) and (pp[0] in range(0, 100)) and (pp[1] in range(0, 100)) and (matrix[pp[0]][pp[1]] != "obstacle"):
				self.possibleTurns.append(i)

	#обнуляем муравья, когда он "заблудился"
	def respawn(self):
		self.x = spawnX
		self.y = spawnY
		self.tabooList = []
		self.putFeromone = False
		self.tabooListIndex = 0
		self.l0 = 0
		if (enableMessages) and (enableLostMessage):
			print("Муравей с номером", self.id, "потерялся!")

	# выбираем куда идти и идём туда
	def turn(self):
		if not self.putFeromone:

			# задаём возможные направления
			if (self.x == 0) and (self.y == 0):
				self.addPossibleTurns([2, 3, 4])
			if (self.x == 0) and (self.y == 99):
				self.addPossibleTurns([0, 1, 2])
			if (self.x == 99) and (self.y == 0):
				self.addPossibleTurns([4, 5, 6])
			if (self.x == 99) and (self.y == 99):
				self.addPossibleTurns([6, 7, 0])
			if (self.x == 0) and (self.y in range(1, 99)):
				self.addPossibleTurns([0, 1, 2, 3, 4])
			if (self.x == 99) and (self.y in range(1, 99)):
				self.addPossibleTurns([0, 4, 5, 6, 7])
			if (self.y == 0) and (self.x in range(1, 99)):
				self.addPossibleTurns([2, 3, 4, 5, 6])
			if (self.y == 99) and (self.x in range(1, 99)):
				self.addPossibleTurns([6, 7, 0, 1, 2])
			if (self.x in range(1, 99)) and (self.y in range(1, 99)):
				self.addPossibleTurns([0, 1, 2, 3, 4, 5, 6, 7])
			
			# вычисляем вероятность хода
			summ = 0
			probabilities = []
			for i in self.possibleTurns:
				summ += self.getInverseDistance(i) ** beta * self.getFeromone(i) ** alpha
			for i in self.possibleTurns:
				probabilities.append(self.getInverseDistance(i) ** beta * self.getFeromone(i) ** alpha / summ )

			if not self.leet:
				# функция подсчитывает сумму первых элементов массива
				def sumFirstElements(arr, end):
					summ = 0
					if end >= len(arr):
						end = len(arr) - 1
					for i in range(0, end):
						summ += arr[i]
					return summ	

				# случайно выбираем направление
				probRange = []
				for i in range(0, len(probabilities)):
					probRange.append(sumFirstElements(probabilities, i))

				def selectDir():
					if (len(self.possibleTurns) > 0):
						rand = r.random()	
						for i in range(len(probRange) - 1):
							if (rand >= probRange[i]) and (rand < probRange[i+1]):
								return self.possibleTurns[i]
						if rand >= probRange[-1]:
							return self.possibleTurns[-1]
					else:
						self.respawn()
			else:
				def selectDir():
					if (len(self.possibleTurns) > 0):
						maxProb = max(probabilities)
						maxIndexes = [i for i, j in enumerate(probabilities) if j == maxProb]
						return self.possibleTurns[r.choice(maxIndexes)]
					else:
						self.respawn()

			newDir = selectDir()
			self.move(newDir)

			if (matrix[self.x][self.y] == "food"):
				leetStr = ""
				if self.leet:
					leetStr = "Это ЭЛИТНЫЙ муравей."
				if enableMessages:
					print("Муравей с номером", self.id, "нашёл", "%#3d" % foodAmounts[foodList.index([self.x, self.y])], "единиц еды на координатах", self.x, self.y, "за", "%#10f" % self.l0, "шагов!", leetStr)
				self.putFeromone = True

				if (initialFoodAmount != 0):
					foodAmounts[foodList.index([self.x, self.y])] -= 1
					if foodAmounts[foodList.index([self.x, self.y])] == 0:
						matrix[self.x][self.y] = initFeromone
						self.putFeromone = False
						if enableMessages:
							print("Еда на координатах", self.x, self.y, "закончилась, а феромон остался!")
				
		else: #if putFeromone
			self.tabooListIndex += 1
			self.x = self.tabooList[-self.tabooListIndex][0]
			self.y = self.tabooList[-self.tabooListIndex][1]

			if type(matrix[self.x][self.y]) == type(0.0):
				newTau = (1 - p) * matrix[self.x][self.y] + q / self.l0
				matrix[self.x][self.y] = newTau

			if (matrix[self.x][self.y] == "spawn"):
				self.respawn()	
		return

# функция рисует точку в виде квадрата в указанных координатах
def drawPoint(color, alpha, x, y):
	s = pg.Surface((scale, scale))  # the size of your rect
	s.set_alpha(alpha)                # alpha level
	s.fill(color)           # this fills the entire surface
	screen.blit(s, (x * scale, y * scale))    # (0,0) are the top-left coordinates
	#pg.draw.rect(screen, color, (x*scale, y*scale, scale, scale), 0)
	return (x*scale, y*scale)

# инициализация поля
def initField():
	for i in range(100):
		matrix.append([])
		for j in range(100):
			matrix[i].append(initFeromone)
	global spawnX
	global spawnY
	spawnX = r.randint(0, 99)
	spawnY = r.randint(0, 99)
	matrix[spawnX][spawnY] = "spawn"

	global foodList
	for i in range(numFood):
		putFoodSuccess = False
		while not putFoodSuccess:
			foodX = r.randint(5, 94)
			foodY = r.randint(5, 94)
			foodXSuccess = (abs(foodX - spawnX) in range(minFoodDistance, maxFoodDistance)) and (abs(foodY - spawnY) in range(0, maxFoodDistance))
			foodYSuccess = (abs(foodY - spawnY) in range(minFoodDistance, maxFoodDistance)) and (abs(foodX - spawnX) in range(0, maxFoodDistance))
			if foodXSuccess or foodYSuccess:
				if [foodX, foodY] not in foodList:
					foodList.append([foodX, foodY])
					foodAmounts.append(initialFoodAmount)
					matrix[foodX][foodY] = "food"
					putFoodSuccess = True
				

	for i in range(numObstacles):
		putObstacleSuccess = 0
		while putObstacleSuccess < numFood + 1: #количество еды + точка спавна
			obstacleX = r.randint(0, 99)
			obstacleY = r.randint(0, 99)
			if not ( (matrix[obstacleX][obstacleY] == "obstacle") and (matrix[obstacleX][obstacleY] == "food") and (matrix[obstacleX][obstacleY] == "spawn")):
				spawnXSuccess = (obstacleX <= spawnX - freeSpace) or (obstacleX >= spawnX + freeSpace)
				spawnYSuccess = (obstacleY <= spawnY - freeSpace) or (obstacleY >= spawnY + freeSpace)
				if spawnXSuccess or spawnYSuccess:
					putObstacleSuccess += 1
				else:
					putObstacleSuccess = 0
					continue
				for i in range(numFood):
					foodX = foodList[i][0]
					foodY = foodList[i][1]
					foodXSuccess = (obstacleX <= foodX - freeSpace) or (obstacleX >= foodX + freeSpace)
					foodYSuccess = (obstacleY <= foodY - freeSpace) or (obstacleY >= foodY + freeSpace)
					if foodXSuccess or foodYSuccess:
						putObstacleSuccess += 1
					else:
						putObstacleSuccess = 0
						continue
		matrix[obstacleX][obstacleY] = "obstacle"

# отрисовка поля
def drawField():
	screen.fill(WHITE)
	for i in range(100):
		for j in range(100):
			if matrix[i][j] == "spawn":
				drawPoint(BLUE, 255, i, j)
			elif matrix[i][j] == "food":
				if (initialFoodAmount > 0):
					foodAlpha = foodAmounts[foodList.index([i, j])] / initialFoodAmount * 200 + 55
				else:
					foodAlpha = 255
				drawPoint(RED, foodAlpha, i, j)
			elif matrix[i][j] == "obstacle":
				drawPoint(BLACK, 20, i, j)
			else:
				feromoneGray = 255 - (matrix[i][j] - initFeromone) * 1.4
				feromoneGreen = 2 * feromoneGray
				if (feromoneGray > 255):
					feromoneGray = 255
				if (feromoneGray < 0):
					feromoneGray = 0
				if (feromoneGreen > 255):
					feromoneGreen = 255
				if (feromoneGreen < 50):
					feromoneGreen = 50
				drawPoint((feromoneGray, feromoneGreen, feromoneGray), 255, i, j)

# инициализация муравьёв
def createAnts():
	numLeet = int(leetQ / 100 * numAnts) # кол-во элитных муравьев

	for i in range(numAnts):
		ants.append(Ant(spawnX, spawnY, False))
	
	# случайная "коронация" муравьев
	while (numLeet > 0):
		leetCandidate = r.choice(ants)
		if not leetCandidate.leet: 
			leetCandidate.leet = True
			numLeet -= 1
			if enableMessages:
				print("Муравью с номером", "%#10d" % leetCandidate.id, "повезло! Он стал ЭЛИТНЫМ.")

# отрисовка и  ход муравьёв
def drawAndMoveAnts():
	for ant in ants:
		ant.turn()
		if enableDrawAnts:
			if not ant.leet:
				drawPoint(BLACK, 70, ant.x, ant.y)
			else:
				drawPoint(TEAL, 127, ant.x, ant.y)

# глобальное испарение феромона
def globalEvaporate():
	for i in range(100):
		for j in range(100):
			if type(matrix[i][j]) == type(0.0):	
				matrix[i][j] *= (1 - gp);


def noFood():
	if initialFoodAmount > 0:
		for i in foodAmounts:
			if i > 0:
				return False
		return True
	else:
		return False

def inc():
	global iterations
	iterations += 1

# точка входа
def main():
	initField()
	createAnts()
	
	running = True
	while running:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
					# пишем свой код
		drawField()
		drawAndMoveAnts()
		pg.display.flip()
		clock.tick()
		globalEvaporate()
		inc()
		if noFood():
			global enableMessages
			if (enableMessages):
				print("Муравьи съели всю еду! На это им потребовалось", iterations, "итераций.")
				enableMessages = False
	pg.quit()

main()