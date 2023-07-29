"""
    get_links.py

    MediaWiki API Demos
    Demo of `Links` module: Get all links on the given page(s)

    MIT License
"""
import requests
import time
import collections

HEIGHTLIMIT = 5
foundGoal = False;
lnkCntDepth = 0
lnkCntBreadth = 0
lnksSeen = set()
lnksCont = []

S = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"

# API is case insensitive. So going to make everything lower case for easy string matching.
print("Article Title to Start at:")
startTitle = input().lower()
print("Article Title to Find:")
goalTitle = input().lower()

bannedLinks = ["category", "template", "help", "portal", "module", "wikipedia", "file"]
if startTitle == goalTitle:
    print("Error: Start and Goal are the same.")

elif any([x in startTitle for x in bannedLinks]):
    print("Error: Starting title is invalid.")

elif any([x in goalTitle for x in bannedLinks]):
    print("Error: Goal title is invalid.")


# API calls can be made for up to 50 titles at once.
def createPARAMS(titleList):
    titleGroup = ""
    heightList = []
    for i in range(min(49, len(titleList) - 1)):
        title, height = titleList.pop(0)
        titleGroup = title + "|"
        heightList.append(height)

    title, height = titleList.pop(0)
    titleGroup = title
    heightList.append(height)

    PARAMS = {
        "action": "query",
        "format": "json",
        "titles": titleGroup,
        "prop": "links",
        "pllimit": "max"
    }
    return PARAMS, heightList


# Does the API calling.
def getLinks(titleList):
    PARAMS, heightList = createPARAMS(titleList)

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    PAGES = DATA["query"]["pages"]

    pageLinks = []
    index = 0
    for key, value in PAGES.items():
        if foundGoal:
            return [];

        # No valid links from this page to other pages, so skip.
        if "links" not in value:
            continue

        # Only 500 results can be listed at once for each title.
        # Continue flag is for the group as a whole.
        # Minority of pages (eg 60 in 1300) have links so seperate those out to reduce API calls.
        if "continue" in DATA:
            lnksCont.append([value["title"], heightList[index]])

        extractLinks(value, pageLinks, heightList[index])
        index += 1

    return pageLinks


# Recursive checking. Each call can fetch 500 links at a time.
def contLinks(PARAMS, heightList):
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    PAGES = DATA["query"]["pages"]

    pageLinks = [];
    index = 0
    for key, value in PAGES.items():
        if foundGoal:
            return [];

        if "links" in value:
            extractLinks(value, pageLinks, heightList[index])

        index += 1

    # https://stackoverflow.com/questions/14882571/how-to-get-all-urls-in-a-wikipedia-page
    if "continue" in DATA:
        pageLinks.extend(contSearch(PARAMS, DATA, heightList))

    return pageLinks


def contSearch(PARAMS, DATA, heightList):
    plcontinue = DATA["continue"]["plcontinue"]
    PARAMS["plcontinue"] = plcontinue
    return contLinks(PARAMS, heightList)


def extractLinks(value, pageLinks, height):
    global foundGoal
    for link in value["links"]:
        if foundGoal:
            break;

        linkTitle = link["title"].lower()
        if linkTitle == goalTitle:
            print("Success")
            foundGoal = True;
            break;

        # https://stackoverflow.com/questions/3389574/check-if-multiple-strings-exist-in-another-string
        elif linkTitle not in lnksSeen and not any([x in linkTitle for x in bannedLinks]):
            lnksSeen.add(linkTitle)
            pageLinks.append([linkTitle, height + 1])


def breadthFirstSearch():
    t0 = time.time()
    global foundGoal
    height = 0

    TOCHECK = []
    NXTLIST = [["Albert Einstein", 0]]

    while height <= HEIGHTLIMIT and not foundGoal:
        TOCHECK = NXTLIST.copy()
        NXTLIST.clear()
        while len(TOCHECK) > 0:
            NXTLIST.extend(getLinks(TOCHECK))

        while len(lnksCont) > 0:
            PARAMS, heightList = createPARAMS(lnksCont)
            NXTLIST.extend(contLinks(PARAMS, heightList))

        print("loop" + str(height))
        height += 1

    t1 = time.time()
    print(str(t1 - t0) + " seconds")
    print("# of Links to check next: " + str(len(NXTLIST)))
    print("# of Links seen total: " + str(len(lnksSeen)))

def weightedDFS(goal, max_height):

    t0 = time.time()
    stack = collections.deque([(startTitle, 0)])
    list_titles = []
    TOCHECK = []

    while stack:
        current_link, height = stack.pop()

        if height < HEIGHTLIMIT:
            TOCHECK.append((current_link, height))
            print(str(TOCHECK))

        if len(TOCHECK) == 50 or len(stack) == 0 and len(TOCHECK) > 0:
            list_titles.extend(getLinks(TOCHECK))
            while len(list_titles) > 0:
                stack.append(list_titles.pop())

        if len(lnksCont) >= 50 or len(stack) == 0 and len(lnksCont) > 0:
            PARAMS, heightList = createPARAMS(lnksCont)
            list_titles.extend(contLinks(PARAMS, heightList))

    t1 = time.time()
    print(str(t1 - t0) + " seconds")
