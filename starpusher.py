import copy
import os
import random
import sys

import pygame
from pygame.locals import *

FPS = 30  # Quadros por segundo para atualizar a tela
WINWIDTH = 1024  # Largura da janela do programa, em pixels
WINHEIGHT = 768  # Altura em pixels
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

# A largura e altura totais de cada bloco em pixels
TILEWIDTH = 50
TILEHEIGHT = 85
TILEFLOORHEIGHT = 40

CAM_MOVE_SPEED = 5  # Quantos pixels por quadro a câmera move

# A porcentagem de azulejos ao ar livre que possuem
# decoração neles, como uma árvore ou pedra
OUTSIDE_DECORATION_PCT = 20

BRIGHTBLUE = (0, 170, 255)
WHITE = (255, 255, 255)
BGCOLOR = BRIGHTBLUE
TEXTCOLOR = WHITE

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'


def main():
    global FPSCLOCK, DISPLAYSURF, IMAGESDICT, TILEMAPPING, OUTSIDEDECOMAPPING, BASICFONT, PLAYERIMAGES, currentImage

    # Inicialização de Pygame e configuração básica das variáveis globais
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    # Como o objeto Surface armazenado em DISPLAYSURF foi retornado
    # da função pygame.display.set_mode (), esse é o
    # Objeto de superfície que é desenhado na tela do computador real
    # quando pygame.display.update () é chamado.
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))

    pygame.display.set_caption('Star Pusher')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)

    # Um valor de ditado global que conterá tudo o Pygame
    # Objetos de superfície retornados por pygame.image.load ().
    IMAGESDICT = {
        'uncovered goal': pygame.image.load('images/RedSelector.png'),
        'covered goal': pygame.image.load('images/Selector.png'),
        'star': pygame.image.load('images/Star.png'),
        'corner': pygame.image.load('images/Wall_Block_Tall.png'),
        'wall': pygame.image.load('images/Wood_Block_Tall.png'),
        'inside floor': pygame.image.load('images/Plain_Block.png'),
        'outside floor': pygame.image.load('images/Grass_Block.png'),
        'title': pygame.image.load('images/star_title.png'),
        'solved': pygame.image.load('images/star_solved.png'),
        'princess': pygame.image.load('images/princess.png'),
        'boy': pygame.image.load('images/boy.png'),
        'catgirl': pygame.image.load('images/catgirl.png'),
        'horngirl': pygame.image.load('images/horngirl.png'),
        'pinkgirl': pygame.image.load('images/pinkgirl.png'),
        'robot': pygame.image.load('images/robot.png'),
        'rock': pygame.image.load('images/Rock.png'),
        'short tree': pygame.image.load('images/Tree_Short.png'),
        'tall tree': pygame.image.load('images/Tree_Tall.png'),
        'ugly tree': pygame.image.load('images/Tree_Ugly.png')
    }

    # Esses valores de ditado são globais e mapeiam o caractere que aparece
    # no arquivo de nível do objeto Surface que ele representa.
    TILEMAPPING = {
        'x': IMAGESDICT['corner'],
        '#': IMAGESDICT['wall'],
        'o': IMAGESDICT['inside floor'],
        ' ': IMAGESDICT['outside floor']
    }

    OUTSIDEDECOMAPPING = {
        '1': IMAGESDICT['rock'],
        '2': IMAGESDICT['short tree'],
        '3': IMAGESDICT['tall tree'],
        '4': IMAGESDICT['ugly tree']
    }

    # PLAYERIMAGES é uma lista de todos os personagens possíveis que o jogador pode ser.
    # currentImage é o índice da imagem atual do player.
    currentImage = 0
    PLAYERIMAGES = [
        IMAGESDICT['princess'],
        IMAGESDICT['boy'],
        IMAGESDICT['catgirl'],
        IMAGESDICT['horngirl'],
        IMAGESDICT['pinkgirl'],
        IMAGESDICT['robot']
    ]

    startScreen()  # Mostra a tela de título até o usuário pressionar uma tecla

    # Leia os níveis do arquivo de texto. Veja o readLevelsFile() para
    # detalhes sobre o formato deste arquivo e como criar seus próprios níveis.
    levels = readLevelsFile('Levels.txt')
    currentLevelIndex = 0

    # O loop principal do jogo. Esse loop executa um único nível, quando o usuário
    # termina esse nível, o nível seguinte / anterior é carregado.
    while True:  # main game loop
        # Execute o nível para realmente começar a jogar:
        result = runLevel(levels, currentLevelIndex)

        if result in ('solved', 'next'):
            # Ir para o próximo nível
            currentLevelIndex += 1
            if currentLevelIndex >= len(levels):
                # Se não houver mais níveis, volte ao primeiro.
                currentLevelIndex = 0
        elif result == 'back':
            # Vá para o nível anterior.
            currentLevelIndex -= 1
            if currentLevelIndex < 0:
                # Se não houver níveis anteriores, vá para o último.
                currentLevelIndex = len(levels) - 1
        elif result == 'reset':
            pass  # Fazer nada. O loop chama novamente runLevel() para redefinir o nível


def runLevel(levels, levelNum):
    global currentImage

    levelObj = levels[levelNum]
    mapObj = decorateMap(levelObj['mapObj'], levelObj['startState']['player'])
    gameStateObj = copy.deepcopy(levelObj['startState'])
    mapNeedsRedraw = True  # set to True to call drawMap()
    levelSurf = BASICFONT.render('Level %s de %s' % (levelNum + 1, len(levels)), 1, TEXTCOLOR)
    levelRect = levelSurf.get_rect()
    levelRect.bottomleft = (20, WINHEIGHT - 35)
    mapWidth = len(mapObj) * TILEWIDTH
    mapHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    MAX_CAM_X_PAN = abs(HALF_WINHEIGHT - int(mapHeight / 2)) + TILEWIDTH
    MAX_CAM_Y_PAN = abs(HALF_WINWIDTH - int(mapWidth / 2)) + TILEHEIGHT

    levelIsComplete = False
    # Track how much the camera has moved
    cameraOffsetX = 0
    cameraOffsetY = 0
    # Track if the keys to move the camera are being held down
    cameraUp = False
    cameraDown = False
    cameraLeft = False
    cameraRight = False

    while True:  # main game loop
        # Redefina essas variáveis
        playerMoveTo = None
        keyPressed = False

        for event in pygame.event.get():  # event handling loop
            if event.type == QUIT:
                # O jogador clicou no "X" no canto da janela
                terminate()

            elif event.type == KEYDOWN:
                # Tecla pressionada
                keyPressed = True
                if event.key == K_LEFT:
                    playerMoveTo = LEFT
                elif event.key == K_RIGHT:
                    playerMoveTo = RIGHT
                elif event.key == K_UP:
                    playerMoveTo = UP
                elif event.key == K_DOWN:
                    playerMoveTo = DOWN
                # Defina o modo de movimento da câmera.
                elif event.key == K_a:
                    cameraLeft = True
                elif event.key == K_d:
                    cameraRight = True
                elif event.key == K_w:
                    cameraUp = True
                elif event.key == K_s:
                    cameraDown = True

                elif event.key == K_n:
                    return 'next'
                elif event.key == K_b:
                    return 'back'
                elif event.key == K_ESCAPE:
                    terminate()  # Esc key quits.
                elif event.key == K_BACKSPACE:
                    return 'reset'  # Reset the level
                elif event.key == K_p:
                    # Mude a imagem do player para a próxima
                    currentImage += 1
                    if currentImage >= len(PLAYERIMAGES):
                        # Após a última imagem do player, use a primeira
                        currentImage = 0
                    mapNeedsRedraw = True

            elif event.type == KEYUP:
                # Desativar o modo de movimento da câmera
                if event.key == K_a:
                    cameraLeft = False
                elif event.key == K_d:
                    cameraRight = False
                elif event.key == K_w:
                    cameraUp = False
                elif event.key == K_s:
                    cameraDown = False

        if playerMoveTo != None and not levelIsComplete:
            # Se o jogador apertou uma tecla para mover, faça o movimento
            # (se possível) e empurre as estrelas empurráveis.
            moved = makeMove(mapObj, gameStateObj, playerMoveTo)

            if moved:
                # incrementar o contador de passos.
                gameStateObj['stepCounter'] += 1
                mapNeedsRedraw = True

            if isLevelFinished(levelObj, gameStateObj):
                # nível for resolvido, devemos mostrar o "solved!" imagem.
                levelIsComplete = True
                keyPressed = False

        DISPLAYSURF.fill(BGCOLOR)

        if mapNeedsRedraw:
            mapSurf = drawMap(mapObj, gameStateObj, levelObj['goals'])
            mapNeedsRedraw = False

        if cameraUp and cameraOffsetY < MAX_CAM_X_PAN:
            cameraOffsetY += CAM_MOVE_SPEED
        elif cameraDown and cameraOffsetY > -MAX_CAM_X_PAN:
            cameraOffsetY -= CAM_MOVE_SPEED

        if cameraLeft and cameraOffsetX < MAX_CAM_Y_PAN:
            cameraOffsetX += CAM_MOVE_SPEED
        elif cameraRight and cameraOffsetX > -MAX_CAM_Y_PAN:
            cameraOffsetX -= CAM_MOVE_SPEED

        # Ajuste o objeto Rect do mapSurf com base no deslocamento da câmera.
        mapSurfRect = mapSurf.get_rect()
        mapSurfRect.center = (HALF_WINWIDTH + cameraOffsetX, HALF_WINHEIGHT + cameraOffsetY)

        # Desenhe mapSurf no objeto DISPLAYSURF Surface.
        DISPLAYSURF.blit(mapSurf, mapSurfRect)

        DISPLAYSURF.blit(levelSurf, levelRect)
        stepSurf = BASICFONT.render('Passos: %s' % (gameStateObj['stepCounter']), 1, TEXTCOLOR)
        stepRect = stepSurf.get_rect()
        stepRect.bottomleft = (20, WINHEIGHT - 10)
        DISPLAYSURF.blit(stepSurf, stepRect)

        if levelIsComplete:
            # for resolvido, mostre a opção "solved!" imagem até o player pressionou uma tecla.
            solvedRect = IMAGESDICT['solved'].get_rect()
            solvedRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)
            DISPLAYSURF.blit(IMAGESDICT['solved'], solvedRect)

            if keyPressed:
                return 'solved'

        pygame.display.update()  # desenhe DISPLAYSURF na tela.
        FPSCLOCK.tick()


def isWall(mapObj, x, y):
    """Retorna True se a posição (x, y) em
         o mapa é uma parede; caso contrário, retorne False."""
    if x < 0 or x >= len(mapObj) or y < 0 or y >= len(mapObj[x]):
        return False  # x e y não estão realmente no mapa.
    elif mapObj[x][y] in ('#', 'x'):
        return True  # parede está bloqueando
    return False


def decorateMap(mapObj, startxy):
    """Faz uma cópia do objeto de mapa fornecido e o modifica.
         Aqui está o que é feito para isso:
             * Paredes que são cantos são transformadas em peças de canto.
             * É feita a distinção entre os pisos externo e interno.
             * Decorações de árvores/pedras são adicionadas aleatoriamente aos ladrilhos externos.

         Retorna o objeto de mapa decorado."""

    startx, starty = startxy  # Syntactic sugar

    # Copie o objeto do mapa para não modificar o original passado
    mapObjCopy = copy.deepcopy(mapObj)

    # Remova os caracteres que não são da parede dos dados do mapa
    for x in range(len(mapObjCopy)):
        for y in range(len(mapObjCopy[0])):
            if mapObjCopy[x][y] in ('$', '.', '@', '+', '*'):
                mapObjCopy[x][y] = ' '

    # Preenchimento de inundação para determinar os pisos internos/externos.
    floodFill(mapObjCopy, startx, starty, ' ', 'o')

    # Converta as paredes adjacentes em ladrilhos de canto.
    for x in range(len(mapObjCopy)):
        for y in range(len(mapObjCopy[0])):

            if mapObjCopy[x][y] == '#':
                if (isWall(mapObjCopy, x, y - 1) and isWall(mapObjCopy, x + 1, y)) or \
                        (isWall(mapObjCopy, x + 1, y) and isWall(mapObjCopy, x, y + 1)) or \
                        (isWall(mapObjCopy, x, y + 1) and isWall(mapObjCopy, x - 1, y)) or \
                        (isWall(mapObjCopy, x - 1, y) and isWall(mapObjCopy, x, y - 1)):
                    mapObjCopy[x][y] = 'x'

            elif mapObjCopy[x][y] == ' ' and random.randint(0, 99) < OUTSIDE_DECORATION_PCT:
                mapObjCopy[x][y] = random.choice(list(OUTSIDEDECOMAPPING.keys()))

    return mapObjCopy


def isBlocked(mapObj, gameStateObj, x, y):
    """Retorna True se a posição (x, y) no mapa for
         bloqueado por uma parede ou estrela, caso contrário, retorne False."""

    if isWall(mapObj, x, y):
        return True
    elif x < 0 or x >= len(mapObj) or y < 0 or y >= len(mapObj[x]):
        return True  # x e y não estão realmente no mapa.
    elif (x, y) in gameStateObj['stars']:
        return True  # uma estrela está bloqueando

    return False


def makeMove(mapObj, gameStateObj, playerMoveTo):
    """Dado um objeto de mapa e estado do jogo, veja se é possível o
         jogador para fazer o movimento dado. Se for, altere a configuração do player.
         posição (e a posição de qualquer estrela empurrada). Caso contrário, não faça nada.

         Retorna True se o jogador se moveu, caso contrário, False."""

    # Certifique-se de que o jogador possa se mover na direção que deseja.
    playerx, playery = gameStateObj['player']

    # Esta variável é "syntactic sugar". Digitar "stars" é mais
    # legível do que digitar "gameStateObj['stars']" em nosso código.
    stars = gameStateObj['stars']

    # O código para lidar com cada uma das direções é tão semelhante à parte
    # de adicionar ou subtrair 1 às coordenadas x/y. Podemos
    # simplifique usando as variáveis xOffset e yOffset.
    if playerMoveTo == UP:
        xOffset = 0
        yOffset = -1
    elif playerMoveTo == RIGHT:
        xOffset = 1
        yOffset = 0
    elif playerMoveTo == DOWN:
        xOffset = 0
        yOffset = 1
    elif playerMoveTo == LEFT:
        xOffset = -1
        yOffset = 0

    # Veja se o jogador pode se mover nessa direção.
    if isWall(mapObj, playerx + xOffset, playery + yOffset):
        return False
    else:
        if (playerx + xOffset, playery + yOffset) in stars:
            # Há uma estrela no caminho, veja se o jogador pode empurrá-la.
            if not isBlocked(mapObj, gameStateObj, playerx + (xOffset * 2), playery + (yOffset * 2)):
                # Mova a estrela.
                ind = stars.index((playerx + xOffset, playery + yOffset))
                stars[ind] = (stars[ind][0] + xOffset, stars[ind][1] + yOffset)
            else:
                return False
        # Mover o jogador para cima
        gameStateObj['player'] = (playerx + xOffset, playery + yOffset)
        return True


def startScreen():
    """Exibir a tela inicial (que possui o título e as instruções)
         até o jogador pressionar uma tecla. Retorna Nenhum."""

    # Posicione a imagem do título.
    titleRect = IMAGESDICT['title'].get_rect()
    topCoord = 50  # topCoord tracks where to position the top of the text
    titleRect.top = topCoord
    titleRect.centerx = HALF_WINWIDTH
    topCoord += titleRect.height

    # Infelizmente, o sistema de fonte e texto do Pygame mostra apenas uma linha em
    # por vez, portanto, não podemos usar strings com \n caracteres de nova linha.
    # Então, vamos usar uma lista com cada linha nela.
    instructionText = [
        'Empurre as estrelas sobre as marcas.',
        'Teclas de seta para mover, WASD para controle da câmera, P para mudar de caractere.',
        'Backspace para redefinir o nível, Esc para sair.',
        'N para o próximo nível, B para voltar um nível.'
    ]

    # Comece desenhando uma cor em branco para a janela inteira:
    DISPLAYSURF.fill(BGCOLOR)

    # Desenhe a imagem do título na janela:
    DISPLAYSURF.blit(IMAGESDICT['title'], titleRect)

    # Posicione e desenhe o texto.
    for i in range(len(instructionText)):
        instSurf = BASICFONT.render(instructionText[i], 1, TEXTCOLOR)
        instRect = instSurf.get_rect()
        topCoord += 10  # Serão 10 pixels entre cada linha de texto.
        instRect.top = topCoord
        instRect.centerx = HALF_WINWIDTH
        topCoord += instRect.height  # Ajuste para a altura da linha.
        DISPLAYSURF.blit(instSurf, instRect)

    while True:  # Loop principal para a tela inicial.
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return  # usuário pressionou uma tecla, então retorne.

        # Exiba o conteúdo do DISPLAYSURF na tela real.
        pygame.display.update()
        FPSCLOCK.tick()


def readLevelsFile(filename):
    assert os.path.exists(filename), 'Arquivo dos Levels nao foi encontrado: %s' % (filename)
    mapFile = open(filename, 'r')
    # Cada nível deve terminar com uma linha em branco
    content = mapFile.readlines() + ['\r\n']
    mapFile.close()

    levels = []  # Irá conter uma lista de objetos de nível.
    levelNum = 0
    mapTextLines = []  # contém as linhas para o mapa de um único nível.
    mapObj = []  # o objeto de mapa criado a partir dos dados em mapTextLines

    for lineNum in range(len(content)):
        # Processe cada linha que estava no arquivo de nível.
        line = content[lineNum].rstrip('\r\n')

        if ';' in line:
            # Ignore as linhas com ;, são comentários no arquivo de levels.
            line = line[:line.find(';')]

        if line != '':
            # Esta linha faz parte do mapa.
            mapTextLines.append(line)
        elif line == '' and len(mapTextLines) > 0:
            # Uma linha em branco indica o final do mapa de um nível no arquivo.
            # Converta o texto em mapTextLines em um objeto nivelado.

            # Encontre a linha mais longa no mapa.
            maxWidth = -1
            for i in range(len(mapTextLines)):
                if len(mapTextLines[i]) > maxWidth:
                    maxWidth = len(mapTextLines[i])
            # Adicione espaços ao final das linhas mais curtas. este
            # garante que o mapa seja retangular.
            for i in range(len(mapTextLines)):
                mapTextLines[i] += ' ' * (maxWidth - len(mapTextLines[i]))

            # Converter mapTextLines em um objeto de mapa.
            for x in range(len(mapTextLines[0])):
                mapObj.append([])

            # Percorra os espaços no mapa e encontre @,. E $
            # caracteres para o estado inicial do jogo.
            for y in range(len(mapTextLines)):
                for x in range(maxWidth):
                    mapObj[x].append(mapTextLines[y][x])

            startx = None  # X e y para a posição inicial do jogador
            starty = None
            goals = []  # lista de (x, y) tuplas para cada objetivo.
            stars = []  # lista de (x, y) para a posição inicial de cada estrela.

            for x in range(maxWidth):
                for y in range(len(mapObj[x])):
                    if mapObj[x][y] in ('@', '+'):
                        # '@' é jogador, '+' é jogador e objetivo
                        startx = x
                        starty = y

                    if mapObj[x][y] in ('.', '+', '*'):
                        # '.' é objetivo, '*' é estrela e objetivo
                        goals.append((x, y))

                    if mapObj[x][y] in ('$', '*'):
                        # '$' é uma estrela
                        stars.append((x, y))

            # Verificações básicas de sanidade do projeto:
            assert startx != None and starty != None, 'O nível %s (em torno da linha %s) em %s está faltando um "@" ou "+" para marcar o ponto inicial.' % (
            levelNum + 1, lineNum, filename)
            assert len(goals) > 0, 'O nível %s (em torno da linha %s) em %s deve ter pelo menos uma meta.' % (
            levelNum + 1, lineNum, filename)
            assert len(stars) >= len(
                goals), 'O nível %s (em torno da linha %s) em %s é impossível de resolver. Possui %s objetivos, mas apenas %s estrelas.' % (
            levelNum + 1, lineNum, filename, len(goals), len(stars))

            # Criar um objeto nivelado e iniciar o estado do jogo.
            gameStateObj = {
                'player': (startx, starty),
                'stepCounter': 0,
                'stars': stars
            }

            levelObj = {
                'width': maxWidth,
                'height': len(mapObj),
                'mapObj': mapObj,
                'goals': goals,
                'startState': gameStateObj
            }

            levels.append(levelObj)

            # Redefina as variáveis para ler o próximo mapa.
            mapTextLines = []
            mapObj = []
            gameStateObj = {}
            levelNum += 1

    return levels


def floodFill(mapObj, x, y, oldCharacter, newCharacter):
    """Altera qualquer valor que corresponda a oldCharacter no objeto de mapa para
         newCharacter na posição (x, y) e faz o mesmo para o
         posições à esquerda, direita, baixo e cima de (x, y), recursivamente."""

    # Neste jogo, o algoritmo de preenchimento cria o interior / o exterior
    # distinção de piso. Esta é uma função "recursiva".
    # Para obter mais informações sobre o algoritmo Flood Fill, consulte:
    #   http://en.wikipedia.org/wiki/Flood_fill
    if mapObj[x][y] == oldCharacter:
        mapObj[x][y] = newCharacter

    if x < len(mapObj) - 1 and mapObj[x + 1][y] == oldCharacter:
        floodFill(mapObj, x + 1, y, oldCharacter, newCharacter)

    if x > 0 and mapObj[x - 1][y] == oldCharacter:
        floodFill(mapObj, x - 1, y, oldCharacter, newCharacter)

    if y < len(mapObj[x]) - 1 and mapObj[x][y + 1] == oldCharacter:
        floodFill(mapObj, x, y + 1, oldCharacter, newCharacter)

    if y > 0 and mapObj[x][y - 1] == oldCharacter:
        floodFill(mapObj, x, y - 1, oldCharacter, newCharacter)


def drawMap(mapObj, gameStateObj, goals):
    """Desenha o mapa para um objeto Surface, incluindo o jogador e
         estrelas. Esta função não chama pygame.display.update (), nem
         ele desenha o texto "Nível" e "Etapas" no canto."""

    # mapSurf será o único objeto Surface que os blocos serão desenhados
    # on, para que seja fácil posicionar o mapa inteiro no DISPLAYSURF
    # Objeto de superfície. Primeiro, a largura e a altura devem ser calculadas.
    mapSurfWidth = len(mapObj) * TILEWIDTH
    mapSurfHeight = (len(mapObj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
    mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
    mapSurf.fill(BGCOLOR)

    # Desenhe os sprites de ladrilhos nessa superfície.
    for x in range(len(mapObj)):
        for y in range(len(mapObj[x])):
            spaceRect = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT, TILEWIDTH, TILEHEIGHT))

            if mapObj[x][y] in TILEMAPPING:
                baseTile = TILEMAPPING[mapObj[x][y]]
            elif mapObj[x][y] in OUTSIDEDECOMAPPING:
                baseTile = TILEMAPPING[' ']

            # Primeiro desenhe o piso de base/parede.
            mapSurf.blit(baseTile, spaceRect)

            if mapObj[x][y] in OUTSIDEDECOMAPPING:
                # Desenhe qualquer decoração de árvore/pedra que esteja nesse ladrilho.
                mapSurf.blit(OUTSIDEDECOMAPPING[mapObj[x][y]], spaceRect)
            elif (x, y) in gameStateObj['stars']:
                if (x, y) in goals:
                    # Um objetivo E estrela estão neste espaço, primeiro o objetivo.
                    mapSurf.blit(IMAGESDICT['covered goal'], spaceRect)
                # Em seguida, desenhe o sprite estrela.
                mapSurf.blit(IMAGESDICT['star'], spaceRect)
            elif (x, y) in goals:
                # Desenhe um objetivo sem uma estrela nele.
                mapSurf.blit(IMAGESDICT['uncovered goal'], spaceRect)

            # Último desenhe o jogador no tabuleiro.
            if (x, y) == gameStateObj['player']:
                # Nota: o valor "currentImage" refere-se
                # para uma tecla em "PLAYERIMAGES" que possui o
                # imagem específica do jogador que queremos mostrar.
                mapSurf.blit(PLAYERIMAGES[currentImage], spaceRect)

    return mapSurf


def isLevelFinished(levelObj, gameStateObj):
    """Retorna True se todos os objetivos tiverem estrelas."""

    for goal in levelObj['goals']:
        if goal not in gameStateObj['stars']:
            # Encontrou um espaço com um objetivo, mas nenhuma estrela nele.
            return False
    return True


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
