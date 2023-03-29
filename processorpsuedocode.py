

partials = list()
graveyard = list()
SUCCESS = 1
FAILURE = -1

def processcharacter(char):
    #pass the character to each partial
    for p in partials:
        result = p.processcharacter()
        if result == SUCCESS:
            #Pass a success result up to the above, so that rollback can occur, or whatever else
            return
        if result == FAILURE:
            #move this partial to the graveyard so it can be rolled back later
            pass

DISAPPEAR = -1
SUCCESS = 1
DEAD = 0
def rollback(pointer):
    #pass the rollback to each partial, and the graveyard
    for p in partials, graveyard:
        result = p.rollback(pointer)
        if result == SUCCESS:
            #put partial in main list
            pass
        if result == DISAPPEAR:
            #get rid of partial altogether
            pass
        if result == DEAD:
            #Put partial on the graveyard
            pass

def clear():
    #get rid of all partials and empy graveyard. Happens in pointer placed success cases
    partials = list()
    graveyard = list()