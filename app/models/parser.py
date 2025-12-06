from fastapi import HTTPException
import re

if __name__ != "__main__": from ..models.models import Question
else:                      from models import Question  

# ---------------- Old Test Body Parser ------------------------

VALIDATION=False

def my_assert(x: bool, comment: str) : 
    if not x: 
        raise HTTPException(400, comment)

def parse_test_body(string: str, validation=False)->list[Question]:
    global VALIDATION
    VALIDATION = validation
    RE = r"^=(.*)"
    arr = re.split(RE, string, flags=re.MULTILINE)
    arr = [x.strip() for x in arr if x.strip() != ""]
    if VALIDATION: ######
        my_assert(len(arr[0::2]) == len(arr[1::2]), "Wrong topic division")
        
    pairs = zip(arr[0::2], arr[1::2])    # [(topicName, topicBody)]
    questions = []
    for name, body in pairs:
        topic_questions = parse_topic_body(name, body)
        questions.extend(topic_questions)
    return questions 
   

def parse_topic_body(name, body)->list[Question]:
   RE = r"^([!#])"
   arr = re.split(RE, body, flags=re.MULTILINE)
   arr = [x.strip() for x in arr if x.strip() != ""]
   pairs = zip(arr[0::2], arr[1::2])
   trios = [parse_question(kind, question) for kind, question in pairs]   # [(kind, (text, answers))]
   return [Question(attr=name, kind=t[0], text=t[1], answers=t[2]) for t in trios]

   
def parse_question(kind, quest_body) -> tuple[str, str, str]:
    RE = r"^[\s\S]*?(?=^[+-])"
    match = re.match(RE, quest_body, flags=re.MULTILINE)
    text = quest_body[0:match.span()[1]].strip()
    answers = quest_body[match.span()[1]::].strip()  # "+apple\n-table\n+cherry"
    if VALIDATION: ######
        # count of right answers
        rights = sum(1 if line.startswith('+') else 0 for line in answers.splitlines())  
        my_assert(kind=='!' and rights==1 or kind=='#', f"Kind Error: \n{quest_body}") 
 
    return kind, text, answers


# -------------------------- unit test ------------
T = """

=Цикли

!Чому дорівнює i після закінчення циклу?

let i = 1, n = 10;
while (i < n ) {
    i += 2;
}

-10
+11
-12
-12

#Що достатньо ввести, щоб цикл скінчився?
let x = 1;
while (x <= 10) 
    x = prompt();

-2
-4
-8
+16
+32

"""


if (__name__ == "__main__"):    
    quests = parse_test_body(T, validation=True)
    print(len(quests))

