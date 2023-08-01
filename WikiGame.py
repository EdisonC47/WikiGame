
"""
    get_links.py

    MediaWiki API Demos
    Demo of `Links` module: Get all links on the given page(s)

    MIT License
"""
import requests
import time
import collections

#Background tracking variables.
foundGoal = False;
linksVisited = dict()
lnksCont = []
linksVisited = dict()
bannedLinks = ["category", "template", "help", "portal", "module", "wikipedia", "file"]

#Default settings. Can be changed by user.
DEPTHLIMIT = 5
startTitle = "Albert Einstein"
goalTitle = ""

S = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"

#API calls can be made for up to 50 titles at once.
def createPARAMS(titleList):
    titleGroup = ""
    depthList = []
    for i in range(min(49, len(titleList)-1)):
        title, depth = titleList.pop(0)
        titleGroup = title + "|"
        depthList.append(depth)
    
    title, depth = titleList.pop(0)
    titleGroup = title
    depthList.append(depth)

    PARAMS = {
        "action": "query",
        "format": "json",
        "titles": titleGroup,
        "prop": "links",
        "pllimit": "max"
    }
    return PARAMS, depthList

#Does the API calling.
def getLinks(titleList):
    PARAMS, depthList = createPARAMS(titleList)

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    PAGES = DATA["query"]["pages"]

    pageLinks = []
    index = 0
    for key, value in PAGES.items():
        if foundGoal:
            return [];

        #No valid links from this page to other pages, so skip.
        if "links" not in value:
            continue

        #Only 500 results can be listed at once for each title.
        #Continue flag is for the group as a whole.
        #Minority of pages (eg 60 in 1300) have links so seperate those out to reduce API calls.
        if "continue" in DATA:
             lnksCont.append([value["title"], depthList[index]])

        extractLinks(value, pageLinks, depthList[index])
        index += 1

    return pageLinks

#Recursive checking. Each call can fetch 500 links at a time.
def contLinks(PARAMS, depthList):
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    PAGES = DATA["query"]["pages"]

    pageLinks = [];
    index = 0
    for key, value in PAGES.items():
        if foundGoal:
            return [];

        if "links" in value:
            extractLinks(value, pageLinks, depthList[index])
            
        index += 1
        
    #https://stackoverflow.com/questions/14882571/how-to-get-all-urls-in-a-wikipedia-page
    if "continue" in DATA:
        pageLinks.extend(contSearch(PARAMS, DATA, depthList))
    
    return pageLinks

def contSearch(PARAMS, DATA, depthList):
    plcontinue = DATA["continue"]["plcontinue"]
    PARAMS["plcontinue"] = plcontinue
    return contLinks(PARAMS, depthList)

def extractLinks(value, pageLinks, depth):
    global foundGoal
    for link in value["links"]:
        if foundGoal:
            break;

        linkTitle = link["title"]
        if linkTitle.lower() == goalTitle.lower() :
            print("Goal Found!")
            foundGoal = True
            linksVisited[goalTitle] = value["title"]
            break;
            
        #https://stackoverflow.com/questions/3389574/check-if-multiple-strings-exist-in-another-string
        elif linkTitle not in linksVisited and not any([x in linkTitle for x in bannedLinks]):
            pageLinks.append([linkTitle, depth + 1])
            linksVisited[linkTitle] = value["title"]

def searchWikipedia(useStack):
    global foundGoal
    foundGoal = False;
    lnksCont.clear()
    linksVisited.clear()

    t0 = time.time()
    deck = collections.deque([(startTitle, 0)])
    listData = collections.deque()
    listTitles = []
    numChecked = 0

    while deck and not foundGoal:
        #DFS uses Stack. BFS uses Queue.
        if (useStack):
            current_link, depth = deck.pop()
        else: 
            current_link, depth = deck.popleft()
        
        if depth <= DEPTHLIMIT:
            listTitles.append((current_link, depth))
            numChecked += 1

        if len(listTitles) >= 50 or len(deck) == 0 and len(listTitles) > 0:
            listData.extend(getLinks(listTitles))

        if len(lnksCont) >= 50 or len(deck) == 0 and len(lnksCont) > 0:
            PARAMS, depthList = createPARAMS(lnksCont)
            listData.extend(contLinks(PARAMS, depthList))

        while len(listData) > 0:
            deck.append(listData.popleft())

    t1 = time.time()
    if foundGoal:
        printPath()
    printData(t1-t0, numChecked, len(linksVisited))

def printPath():
    global linksVisited
    titleStack = []
    currentTitle = goalTitle
    while currentTitle != startTitle:
        titleStack.append(currentTitle)
        currentTitle = linksVisited[currentTitle]

    titlePath = startTitle
    while titleStack:
        titlePath += " -> " + titleStack.pop()

    print (titlePath)

def printData(time, checked, seen):
    print(str(time) + " seconds")
    print("# of Titles used for API calls: " + str(checked))
    print("# of Titles seen total: " + str(seen))

def getUserTitle(otherTitle):
    userTitle = input().strip()
    if not userTitle:
        print("Selection is blank, please choose another:")
        return getUserTitle(otherTitle)

    elif any([x in userTitle for x in bannedLinks]):
        print("Not a valid selection, please choose another:")
        return getUserTitle(otherTitle)

    elif userTitle == otherTitle:
        print("Start and End title would be the same, please choose another: ")
        return getUserTitle(otherTitle)

    return userTitle;

def runSearches():
    print("Starting Title: " + startTitle)
    print("Goal Title: " + goalTitle)
    print("Max Depth: " + str(DEPTHLIMIT))
    print()
    print("Starting Depth First Search.")

    #depthFirstSearch()
    searchWikipedia(True)

    print()
    print("Starting Breadth First Search.")
    #breadthFirstSearch()
    searchWikipedia(False)

print("Welcome to the Wikigame automated search!")
userInput = ""
while userInput != "7":
    print()
    print("Select an Option:")
    print("1. Set title to start at.")
    print("2. Set title to search for.")
    print("3. Swap titles.")
    print("4. See currently selected titles.")
    print("5. Set maximum depth.")
    print("6. Execute Searches.")
    print("7. See Credits.")
    print("8. Exit")
    userInput = input();
    print();

    if userInput == "1":
        print("Disclaimer: Starting Title is case sensitive.")
        print("Name of title to start at: ")
        userTitle = getUserTitle(goalTitle)
        startTitle = userTitle;
    
    elif userInput == "2":
        print("Name of title to search for: ")
        userTitle = getUserTitle(startTitle)
        goalTitle = userTitle;

    elif userInput == "3":
        tempTitle = startTitle;
        startTitle = goalTitle;
        goalTitle = tempTitle;
        print("Starting Title: " + startTitle)
        print("Goal Title: " + goalTitle)

    elif userInput == "4":
        print("Starting Title: " + startTitle)
        print("Goal Title: " + goalTitle)
    
    elif userInput == "5":
        print("Current Max Depth: " + str(DEPTHLIMIT))
        print("New Max Depth: ")
        DEPTHLIMIT = int(input())

    elif userInput == "6":
        runSearches()

    elif userInput == "7":
        print("Axel Lynch - for functions utilizing Wikipedia API.")
        print("Edison Chueung - for optimizing the search algorithms.")
        print("Patrick Nguyen - for project planning and documentation.")

    elif userInput == "8":
        break;

    else:
        print("No valid option selected.")