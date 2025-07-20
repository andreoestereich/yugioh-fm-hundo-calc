#!/bin/env python

import mysql.connector
from sys import argv
from os.path import isfile

import pandas as pd

#Multipliyer for techs since they take longer
SA_TECH_TIME = 4

FUSIONS_TO_SHOW = 5

#card list categories
mustDrop = set([1, 4, 16, 19, 20, 21, 26, 35, 38, 54, 82, 91, 103, 147, 338, 349, 350, 370, 371, 372, 373, 386, 391, 653, 707, 712, 713, 714])
shouldDrop = set([3, 5, 9, 13, 23, 24, 32, 34, 36, 40, 42, 45, 49, 50, 53, 55, 58, 75, 77, 79, 80, 81, 83, 85, 86, 87, 88, 90, 93, 95, 96, 98, 105, 106, 122, 123, 124, 125, 126, 130, 140, 152, 167, 170, 177, 186, 192, 193, 196, 199, 200, 205, 206, 207, 213, 218, 223, 227, 230, 243, 247, 251, 258, 265, 270, 289, 292, 296, 298, 300, 303, 312, 313, 314, 315, 316, 317, 319, 321, 325, 327, 330, 331, 332, 333, 334, 335, 337, 345, 347, 368, 379, 387, 388, 393, 395, 397, 398, 399, 402, 405, 407, 408, 411, 419, 422, 424, 431, 436, 437, 453, 464, 465, 466, 469, 472, 475, 484, 500, 504, 509, 516, 521, 522, 526, 527, 538, 547, 548, 552, 558, 563, 572, 573, 575, 577, 596, 618, 619, 625, 635, 636, 645, 657, 658])
shouldBuy = set([66, 102, 112, 146, 153, 165, 234, 241, 275, 367, 378, 381, 382, 383, 384, 385, 389, 394, 427, 433, 435, 442, 480, 494, 543, 566, 580, 581, 586, 588, 592, 607, 616, 665, 666, 673])
mustFuse = set([ 22, 37, 64, 69, 72, 217, 318, 348, 545, 667, 669, 689, 696])
shouldFuse = set([2, 10, 11, 15, 31, 33, 39, 41, 73, 84, 97, 99, 100, 117, 133, 138, 154, 157, 168, 215, 244, 272, 294, 301, 302, 304, 305, 306, 307, 308, 309, 310, 311, 320, 322, 323, 324, 326, 328, 329, 336, 340, 341, 342, 346, 375, 376, 377, 390, 392, 401, 404, 409, 412, 413, 423, 425, 426, 430, 434, 438, 440, 443, 448, 449, 450, 456, 458, 459, 460, 462, 467, 471, 473, 479, 483, 487, 495, 502, 508, 511, 518, 519, 520, 529, 531, 533, 546, 551, 564, 567, 570, 571, 582, 587, 593, 594, 595, 610, 613, 617, 620, 626, 627, 633, 638, 639, 641, 642, 643, 647, 650, 651, 654, 656, 659, 660, 661, 662, 663, 664, 668, 670, 671, 672, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 690, 691, 692, 693, 694, 695, 697, 698, 699, 700])
rituals = set([ 356, 357, 360, 364, 365, 374, 380, 701, 702, 703, 704, 705, 706, 708, 710, 715, 716, 718, 719, 720])
unoptainable = set([ 7, 17, 18, 28, 51, 52, 56, 57, 60, 62, 63, 67, 235, 252, 284, 288, 299, 369, 428, 429, 499, 541, 554, 555, 562, 603, 628, 640, 709, 711, 717, 721, 722])
dropable = set([i for i in range(1,723) if i not in unoptainable ])

def cardName(cid):
    return cardNames[cid-1]

def readMemCard(memFilePath):
    def hex2int(hex):
        return int(hex[1])*256 + int(hex[0])

    #memcardBlockSize = 0x2000
    gameNameOffset = 0x0097
    deckOffsetSize = 0x2200
    libraryOffsetSize = 0x2cbc
    starshipOffsetSize = 0x27e0
    #freeDuelCountOffset = 0x2720

    deckList = list()
    with open(memFilePath, mode='rb') as memcard:
        memcard.seek(gameNameOffset)
        byte = memcard.read(6)
        if byte != b'YUGIOH':
            print("No game data.")
            exit()

        memcard.seek(deckOffsetSize)
        #deck  = memcard.read(0x0050)
        for _ in range(40):
            card  = hex2int(memcard.read(0x0002))
            deckList.append(card)
        vault = [ int(i) for i in  memcard.read(722) ]
        for card in deckList:
            vault[card-1] += 1

        memcard.seek(libraryOffsetSize)
        libraryCards = set()
        card = 0
        while card < 723:
            byte = memcard.read(1)[0]
            for i in range(8):
                #Look at the bit and at the voult cause the game doesn't update library without opening it
                if card > 0 and card < 723 and (byte << i & 0x80 or vault[card-1]):
                    libraryCards.add(card)
                card += 1
        memcard.seek(starshipOffsetSize)
        starships = hex2int(memcard.read(2))

        #freeBattleCount = list()
        #memcard.seek(freeDuelCountOffset)
        #for i in range(39):
        #    wins = hex2int(memcard.read(2))
        #    loses = hex2int(memcard.read(2))
        #    freeBattleCount.append((wins, loses))
            
    return (libraryCards, vault, starships)

def cleanFetch():
    return list(map(lambda x:x[0], mycursor.fetchall()))

def requires(oponID, reqlist):
    haveNots = list()
    for cardId in reqlist:
        if cardId not in cardsInLib:
            haveNots.append(cardId)
    if len(haveNots) == 0 :
        return True
    cards = ', '.join(map(str,haveNots))
    sqlCMD = 'SELECT ranking, SUM(prob) as pb FROM `Droplist` WHERE cid in (%s) AND oponent = %i GROUP BY ranking ORDER BY pb DESC'%(cards, oponID)
    mycursor.execute(sqlCMD)
    print(oponNames[oponID-1], end='')
    for rank, prob in mycursor.fetchall():
        print(" %s (%i),"%(rankNames[rank-1], prob), end='')
    for cardId in haveNots:
        print(" %03d %s;"%(cardId, cardNames[cardId-1]),end='')
    print("\n")
    return False

def preReqs():
    done = True
    #"Pegasus"
    done = requires(15, [657]) and done
    #"Jono 2nd"
    done = requires(20, [82]) and done
    #"Heieshin"
    done = requires(8, [372,373,371,370]) and done
    #"Seto 3rd"
    done = requires(36, [1,424,619]) and done
    #"Seto 2nd"
    done = requires(32, [565,622,624,493,507,447,474,583,515]) and done
    #"Darknite"
    done = requires(37, [575]) and done
    #"Bakura"
    done = requires(14, [433]) and done
    #"Teana"
    done = requires(2, [543,566]) and done
    #"Kaiba" 
    done = requires(17, [66,163,151]) and done
    #"Martis"
    done = requires(28, [378]) and done


    #requires("Villager1 SAPow", [(338,32)])
    #requires("Rex SAPow", [(308,18)])
    #requires("Seto 2nd SAPow", [(21,8),(645,12),(565,12),(622,12),(624,12),(493,26),(507,26),(447,26),(474,44),(583,26),(515,26)])
    #requires("Keith BCD", [(319,64),(658,60)])
    #requires("Bakura BCD", [(350,32),(433,10)])
    #requires("Kaiba SAPow", [(630,12),(297,12),(454,12),(216,12),(418,12),(275,12),(614,12),(66,12),(128,12),(578,12),(163,12),(498,12),(281,12),(287,12),(151,12),(517,12),(621,12),(249,12)])
    #requires("Weevil SAPow", [(367,5)])
    #requires("Meadow Mage SAPow", [(713,20),(707,20)])
    #requires("Nitemare Atech", [(347,60),[(341,30),(342,30)]])
    #requires("Mai Atech", [(317,72)])
    #requires("Meadow Mage Atech", [(345,64),(349,64),(313,64),(314,64),(301,64)])
    #requires("Mage Soldier Atech", [(321,40)])
    #requires("Keith Atech", [(320,64)])

    return done

def mDrop(cardlist):
    if len(cardlist) == 0:
        return
    idStr = ""
    for card in cardlist:
        idStr += '%i,'%(card)
    sqlCMD = 'SELECT * FROM `Droplist` WHERE cid IN (' + idStr[:-1] + ') ORDER BY oponent,ranking'

    mycursor.execute(sqlCMD)

    oponProbs = dict()
    dropList = mycursor.fetchall()
    for cid,oponent,rank,prob in dropList: 
        if rank == 3:
            prob = prob/techTime
        if (oponent,rank) in oponProbs.keys():
            oponProbs[(oponent,rank)] += prob
        else:
            oponProbs[(oponent,rank)] = prob
    oponProbs = sorted(oponProbs.items(), key=lambda item: item[1], reverse=True)
    for i in range(min(len(oponProbs),10)):
        oponId,rankId = oponProbs[i][0]
        print(oponNames[oponId-1] + "-" + rankNames[rankId-1] + ": %i"%(oponProbs[i][1]))
        for cid,oponent,rank,prob in dropList:
            if oponent == oponId and rank == rankId:
                print(cardNames[cid-1]+', ', end='')
        print('\n')

    return len(dropList) == 0

def sdrop():
    idStr = ""
    for card in dropable:
        idStr += '%i,'%(card)
    sqlCMD = 'SELECT Droplist.cid,Droplist.oponent,Droplist.ranking,Droplist.prob,Cards.stars FROM `Droplist` JOIN `Cards` ON `Cards`.cid=`Droplist`.cid WHERE Droplist.cid IN '
    sqlCMD += '(' + idStr[:-1] + ')' 
    mycursor.execute(sqlCMD)

    print("\n---Drops---")
    cols = ["cid", "oponent", "rank", "prob", "stars"]
    dropList = pd.DataFrame(mycursor.fetchall(), columns=cols)

    dropList = dropList[~dropList["oponent"].isin([35, 39])]

    dropList["value"] = dropList["prob"]*dropList["stars"]
    dropList["value"] = dropList["value"].astype("float64")
    maskSAtech = dropList["rank"] == 3
    dropList.loc[maskSAtech, "value"] = dropList["value"][maskSAtech].div(SA_TECH_TIME)

    dropList["cardName"] = dropList["cid"].map(cardName)
    dropList = dropList.sort_values("stars", ascending=False)

    oponValue = dropList.groupby(["oponent", "rank"]).sum("value")
    oponValue = dropList.sort_values("value", ascending=False)

    for index, row in oponValue.head(4).iterrows():
        print(f'{oponNames[int(row["oponent"])-1]} - {rankNames[int(row["rank"])-1]} ({row["value"]:,.0f})')
        dropMask = (dropList["oponent"] == row["oponent"]) & (dropList["rank"] == row["rank"])
        cols = ["cardName", "cid", "prob", "stars"]
        print(dropList[dropMask].to_string(columns=cols, index=False))
        print("\n")
    
def fusionChecker(listCards, printUnavail):
    if len(listCards) > 0:
        idStr = ""
        for card in listCards:
            idStr += '%i,'%(card)
        sqlCMD = 'SELECT cid,fusable FROM `Cards` WHERE cid IN '
        sqlCMD += '(' + idStr[:-1] + ')' 
        mycursor.execute(sqlCMD)
        fusList = mycursor.fetchall()

        idStr = ""
        for cid,fusable in fusList:
            if fusable:
                idStr += '%i,'%(cid)
        if len(idStr) > 0:
            print("\n---Fusions---")
            sqlCMD = 'SELECT * FROM `Fusions` WHERE result IN '
            sqlCMD += '(' + idStr[:-1] + ')' 
            mycursor.execute(sqlCMD)
            cols = ["result", "card1", "card2"]
            fusList = pd.DataFrame(mycursor.fetchall(), columns=cols)

            fusList["card1inVault"] = fusList["card1"].map(lambda x: vault[x-1])
            fusList["card2inVault"] = fusList["card2"].map(lambda x: vault[x-1])

            fusList["cardVolum"] = fusList["card1inVault"]*fusList["card2inVault"]
            fusList = fusList.sort_values("cardVolum", ascending=False).drop_duplicates("result").head(FUSIONS_TO_SHOW)
            fusList["resName"] = fusList["result"].map(cardName)
            fusList["c1Name"] = fusList["card1"].map(cardName)
            fusList["c2Name"] = fusList["card2"].map(cardName)

            if fusList.shape[0] < 1:
                return True

            cols = ["resName", "result", "c1Name", "card1", "card1inVault", "c2Name", "card2", "card2inVault"]
            print(fusList.to_string(columns=cols, index=False))
            return False

    return True
    
def ritualsChecker():
    sqlCMD = 'SELECT * FROM `Rituals`;'
    mycursor.execute(sqlCMD)
    ritList = mycursor.fetchall()

    for result,ritual,card1,card2,card3 in ritList:
        if result not in cardsInLib and result not in unoptainable:
            print("%s <<< %s ::: %s + %s + %s"%(cardNames[result-1],cardNames[ritual-1],cardNames[card1-1],cardNames[card2-1],cardNames[card3-1]))

def starsLeft(starCount):
    idStr = ""
    for card in dropable:
        idStr += '%i,'%(card)
    sqlCMD = 'SELECT SUM(stars) AS starTot FROM `Cards` WHERE stars<5000 AND cid IN '
    sqlCMD += '('+ idStr[:-1] + ');'
    mycursor.execute(sqlCMD)
    starsLeft = int(cleanFetch()[0])
    print("Have %i of %i stars needed."%(starCount, starsLeft))
    if starsLeft < starCount:
        codesPrint(dropable)

def codesPrint(listCards):
    if len(listCards) > 0:
        idStr = ""
        for card in listCards:
            idStr += '%i,'%(card)
        sqlCMD = 'SELECT cid,pass FROM `Cards` WHERE cid IN '
        sqlCMD += '(' + idStr[:-1] + ')' 
        mycursor.execute(sqlCMD)
         

        for cid,ccode in mycursor.fetchall(): 
            print("%08i  -- %s"%(ccode, cardNames[cid-1]))

def ordering():
    if not preReqs():
        return

    if not mDrop(mustDrop):
        print("Clear must drop first")
        return

    if fusionChecker(mustFuse, True):
        fusionChecker(dropable, False)

    sdrop()

    return
    print("\n---Rituals---")
    ritualsChecker()

def printUsage():
    print("Just use this right.")

if len(argv) == 2 and isfile(argv[1]):
    savePath = argv[1]
    cardsInLib, vault, stars = readMemCard(savePath)

    #connect to the mysql database
    mydb = mysql.connector.connect(host="localhost",
                                   user="andrelo",
                                   password="",
                                   database="yugiohFM",
                                   charset="utf8mb4",
                                   collation="utf8mb4_general_ci")
    mycursor = mydb.cursor()

    #load relevant info
    mycursor.execute('SELECT cname FROM `Cards`')
    cardNames = cleanFetch()
    mycursor.execute(' SELECT `oponName` FROM `Oponents`;')
    oponNames = cleanFetch()
    rankNames = ["SAPow", "BCD", "SATech"]
    mycursor.execute('SELECT cid FROM `Cards` WHERE (stars > 500000 OR stars = 0) AND fusable = FALSE;')
    mustDrop = cleanFetch()
    mycursor.execute('SELECT cid FROM `Cards` WHERE (stars > 500000 OR stars = 0) AND fusable = TRUE;')
    dbMustFuse = cleanFetch()

    for cid in cardsInLib:
        if cid in dropable:
            dropable.remove(cid)
        if cid in mustDrop:
            mustDrop.remove(cid)
        elif cid in shouldFuse:
            shouldFuse.remove(cid)
        elif cid in shouldBuy:
            shouldBuy.remove(cid)
        elif cid in mustFuse:
            mustFuse.remove(cid)
        elif cid in shouldFuse:
            shouldFuse.remove(cid)
        elif cid in rituals:
            rituals.remove(cid)

    print("%i of 689 obtained!"%(len(cardsInLib)))
    starsLeft(stars)
    ordering()
else:
    printUsage()
