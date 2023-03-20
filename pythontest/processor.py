#Processor functioning:
#Read character
#Pass to instructions
#If an instruction is complete, replace text

#Character results:
#-Failure without reset
#-Failure with individual reset
#-Success with roll-back
#-Success with global reset

#When should we do each of these?
#Is there any reason that we shouldn't roll back?
#-When the cursor is placed afterwards it seems appropriate not to roll back. Perhaps Cursor placement should be tied to reset.
#Should we always reset after a string?
#I think we should never reset before a string


#Expression String rules: 
#Input expressions should only use a string or variable label once.
#There should always be a literal expression between a string and the beginning and end of the expression
#Never have two strings in a row
#String (*) and variable (+) should not end an expression. Doing so not only makes no sense, but will cause an error.
#Failing to follow these rules may result in a crash, and otherwise will result in unexpected behaviour
#The current code is finicky at best, and may fail to recognise matches. I might improve, it, but It'll be serviceable for now.
#["*X"f->*X|], What do I do in the case "a""f? does this map to "a or a"? I think I'll give precedence to the earlier case, so a" is the answer.
#In later revisions, I might instead keep track of multiple possible starting points ("yuck!"). Unfortunately, this could lead to
#branching at the end of every string (exponential yuck!)
#The other problem that remains is what to do when a match is found. Should every other expression be rolled back? Or reset completely? I'll start with resetting.

#Idea: No string branching. Otherwise things like ["*X"times"*Y"->(multiply X and Y)] might recognise something like "1"+"2"times"3" as 1"+"2 multiplied by 3.
#Programmers will just have to avoid prematurely terminating strings. A convention would likely arise of how strings are started and ended. Also, ideally some way of escaping special characters.
#Instead of escaping in-text, they'll have to use escaping in the instructions, some sort of post-replacement.

global_printcommands = False
global_printreplacements = False

STATE_WAITING = 0
STATE_CONTINUING = 1
STATE_DEAD = -1

PROC_SUCCESS = 1 
PROC_CONTINUE = 0
PROC_FAILURE = -1

#Rollback Outcomes
ROLL_SUCCESS = 1  #Rolled Back successfully
ROLL_DEAD = 0     #Still dead, shouldnt be added to active list
ROLL_DELETE = -1  #Rollback went too far, this partial should be deleted.

import sys

class partial:
    def __init__(self, expr) -> None:
        self.pointer = 0
        self.mode = STATE_CONTINUING
        self.posmap = [sys.maxsize for x in expr]
        self.poststring = False
        self.expr = expr
        self.diedat = 0
    
    #Rolls back when a success occurs
    def rollback(self, cp):
        if self.mode == STATE_DEAD:
            if self.diedat < cp:
                return ROLL_DEAD
        self.mode = STATE_CONTINUING
        currentpointer = 0
        if self.posmap[currentpointer] > cp:
            return ROLL_DELETE
        while currentpointer < len(self.expr):
            char = self.expr[currentpointer]
            if self.posmap[currentpointer] < cp:
                currentpointer += 1
                if char == '*' or char == '+':
                    currentpointer += 1
                    if char == '*':
                        self.mode = STATE_WAITING
                else:
                    if char == '~':
                        currentpointer += 1
                    self.mode = STATE_CONTINUING
            else:
                self.pointer = currentpointer
                return ROLL_SUCCESS
        return ROLL_DEAD
            
    
    #Increments the pointer by n, and then continues if a string is met,
    #adjusting the mode as necessary. We assume there will not be two strings in a row.
    def increment(self, n, mode, expr, cp):
        self.posmap[self.pointer] = cp
        self.pointer += n
        self.mode = mode
        if self.pointer == len(expr):
                return
        if expr[self.pointer] == '*':
            self.poststring = True
            self.increment(2, STATE_WAITING, expr, cp)

    def processchar(self, expr, char, cp):
        if self.mode == STATE_WAITING:
            if expr[self.pointer] == '~':
                if expr[self.pointer+1] == char:
                    self.increment(2, STATE_CONTINUING, expr, cp)
                    self.started = True
                    if self.pointer == len(expr):
                        return PROC_SUCCESS
            elif expr[self.pointer] == char:
                self.increment(1, STATE_CONTINUING, expr, cp)
                self.started = True
                if self.pointer == len(expr):
                    return PROC_SUCCESS
            elif expr[self.pointer] == '+': #This occurs after a string
                self.increment(2, STATE_WAITING, expr, cp)
                if self.pointer == len(expr): #This should never happen, as strings should be separated from ends of expressions
                    return PROC_SUCCESS
        elif self.mode == STATE_CONTINUING:
            if expr[self.pointer] == '+':
                self.increment(2, STATE_CONTINUING, expr, cp)
                if self.pointer == len(expr):
                    return PROC_SUCCESS
            elif expr[self.pointer] == '~':
                if expr[self.pointer+1] == char:
                    self.increment(2, STATE_CONTINUING, expr, cp)
                    self.started = True
                    if self.pointer == len(expr):
                        return PROC_SUCCESS
            elif expr[self.pointer] == char:
                self.increment(1, STATE_CONTINUING, expr, cp)
                if self.pointer == len(expr):
                    return PROC_SUCCESS
            else:
                self.mode = STATE_DEAD
                self.diedat = cp
                return PROC_FAILURE
        elif self.mode == STATE_DEAD:
            return PROC_FAILURE
        return PROC_CONTINUE
    
    def apply(self, string : str, expr, replacement):
        pointer = 0
        cp = self.posmap[pointer]
        chardict = dict()
        stringdict = dict()
        firstpoint = self.posmap[0]
        while pointer < len(expr):
            if expr[pointer] == '+':
                chardict[expr[pointer+1]] = string[cp]
                cp += 1
                pointer += 2
                continue
            elif expr[pointer] == '*':
                #We have to find the next literal and work backwards
                i = 1
                while expr[pointer+(2*i)] == '+':
                    i += 1 #counting the number of vars between the string and the next literal
                literalpos = self.posmap[pointer+(2*i)]
                stringdict[expr[pointer+1]] = string[cp:literalpos-i+1]
                cp = literalpos - i + 1
                pointer += 2
                continue
            elif expr[pointer] == '~':
                cp += 1
                pointer += 2
            else:
                cp += 1
                pointer += 1
        represult = ""
        pointer = 0
        newcursor = -1
        while pointer < len(replacement):
            if replacement[pointer] == '*':
                represult += stringdict[replacement[pointer+1]]
                pointer += 2
            elif replacement[pointer] == '+':
                represult += chardict[replacement[pointer+1]]
                pointer += 2
            elif replacement[pointer] == '|':
                newcursor = pointer
                pointer += 1
            elif replacement[pointer] == '~':
                represult += replacement[pointer+1]
                pointer += 2
            else:
                represult += replacement[pointer]
                pointer += 1
        if global_printreplacements:
            print("Replaced string '{}' with '{}' according to command [{}->{}]".format(string[firstpoint:cp].replace("\n", "\\n"), represult.replace("\n", "\\n"), expr.replace("\n", "\\n"), replacement.replace("\n", "\\n")))
        return (firstpoint, string[0:firstpoint] + represult + string[cp:], -1 if newcursor == -1 else firstpoint + newcursor)

class instruction:
    def __init__(self, expr, replacement) -> None:
        self.expr = expr
        self.replacement = replacement
        instruction.checkduplicates(expr, replacement)
        self.partiallist = list()#Keeps track of all the possible starting points
        self.deadlist = list()   #Remembers the failed starting points for rollback

    def duplicate(self):
        return instruction(self.expr, self.replacement)

    #Accepts a character, returns None or a complete partial
    def processchar(self, char, cp):
        self.partiallist.append(partial(self.expr))
        i = 0
        while i < len(self.partiallist):
            result = self.partiallist[i].processchar(self.expr, char, cp)
            if result == PROC_FAILURE:
                died = self.partiallist.pop(i)
                self.deadlist.append(died)
                i -= 1
            elif result == PROC_SUCCESS:
                return self.partiallist[i]
            i += 1
        return None
        
    def rollback(self, cp):
        newpartials = list()
        for partial in self.partiallist:
            result = partial.rollback(cp)
            if result == ROLL_DELETE:
                continue
            elif result == ROLL_SUCCESS:
                newpartials.append(partial)
        i = -1
        while i > -1 - len(self.deadlist) and self.deadlist[i].diedat >= cp:
            partial = self.deadlist.pop(i)
            result = partial.rollback(cp)
            if result == ROLL_DELETE:
                continue
            elif result == ROLL_SUCCESS:
                newpartials.append(partial)
            i -= 1
        self.partiallist = newpartials

    def reset(self):
        self.partiallist = list()
        self.deadlist = list()

    #Maybe in the future, I could support detecting duplicate occurrences, and so duplicates won't matter
    #TODO: Add escapes for characters. This allows special characters (+,*,[,],->) to be used as literals.
    def checkduplicates(expr, replacement):
        pointer = 0
        variables = []
        strings = []
        while pointer < len(expr):
            if expr[pointer] == '+':
                char = expr[pointer + 1]
                if char in variables:
                    raise Exception("Duplicate variable +{} in expression {}".format(char, expr))
                variables.append(char)
                pointer += 2
                continue
            if expr[pointer] == '*':
                char = expr[pointer + 1]
                if char in variables:
                    raise Exception("Duplicate string *{} in expression {}".format(char, expr))
                strings.append(char)
                pointer += 2
                continue
            if expr[pointer] == '~':
                pointer += 2
                continue
            pointer += 1
        pointer = 0
        while pointer < len(replacement):
            if replacement[pointer] == '*':
                if replacement[pointer + 1] not in strings:
                    raise Exception("String *{} in expression {} not declared".format(char, replacement))
                pointer += 1
            if replacement[pointer] == '+':
                if replacement[pointer + 1] not in variables:
                    raise Exception("Variable +{} in expression {} not declared".format(char, replacement))
                pointer += 1
            if replacement[pointer] == '~':
                pointer += 1
            pointer += 1


class processor:
    def __init__(self, instructions=list()) -> None:
        self.instructions = instructions

    def run(self, string):
        cp = 0
        changed = True
        while(changed):
            changed = False
            while cp < len(string):
                char = string[cp]
                if char == '[':
                    string = self.addinstruction(string, cp)
                    continue
                if char == '{':
                    string = self.push(string, cp)
                    continue
                for instruction in self.instructions:
                    result = instruction.processchar(char, cp)
                    if result != None:
                        cp, string, newcp = result.apply(string, instruction.expr, instruction.replacement)
                        if newcp != -1:
                            for instruction in self.instructions:
                                instruction.reset()
                            changed = True
                            cp = newcp - 1
                            break
                        else:
                            for instruction in self.instructions:
                                instruction.rollback(cp)
                            changed = True
                            cp = cp - 1
                            break
                cp += 1
        return string
    
    def addinstruction(self, string : str, cp):
        end = string.index(']', cp)
        while string[end - 1] == '~':
            end = string.index(']', end+1)
        commandstring = string[cp+1:end]
        expr, replacement = commandstring.split('->')
        if global_printcommands:
            print("New Command added: [{}]".format(commandstring))
        self.instructions.append(instruction(expr,replacement))
        return string[:cp] + string[end+1:]
    
    def push(self, string, cp):
        end = string.index('}', cp)
        substring = string[cp+1:end]
        instlist = list()
        for inst in self.instructions:
            instlist.append(inst.duplicate())
        subprocessor = processor(instlist)
        repstring = subprocessor.run(substring)
        return string[:cp] + repstring + string[end+1:]

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="FAR", description="Interpreted for the FAR programming language")
    parser.add_argument("input", help="Program to be run")
    parser.add_argument("output", help="File for output to be written to. May be the same as input.")
    parser.add_argument("-printoutput", action="store_true", help="Prints output on completion.")
    parser.add_argument("-printreplacement", action="store_true", help="Prints upon every replacement that occurs")
    args = parser.parse_args()
    infilename = args.input
    outfilename = args.output
    global_printreplacements = args.printreplacement

    proc = processor()
    infile = open(infilename, "r")
    instring = infile.read()
    infile.close()
    string = proc.run(instring)
    if args.printoutput:
        print(string)
    file = open(outfilename, "w")
    file.write(string)
    file.close()