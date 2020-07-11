import os
from flask import Flask, request

server = Flask(__name__)

@server.route('/', methods=['GET'])
def test():
    return "<b>hello</b>", 200

# if __name__ == '__main__':
#     server.debug = True
#     server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

import vk_api
import datetime

#from LatexMethods import LatexMethods
#from config import SSmembers
#from libraries.num2text import num2text


class SumStringsFloat(object):
    def __add__(self, other):
        return float(other)


class Config:
    sign_path = '/home/darkydash/PycharmProjects/StudSovet/latex/sign.png'
    login = ''
    password = ''
    session_place = 'Интернет'
    wall_url = 'wall-90904335_5231'
    session_number = '01072019/1НИУВШЭ'
    session_date = str(datetime.datetime.now().day) + '.' + str(datetime.datetime.now().month) + '.' + (datetime.datetime.now().year)
    session_description = """Голосование о прекращении полномочий секретаря студенческого совета НИУ ВШЭ, Быкова Кирилла"""  # ...
    session_vote_description = """Быкова К.В. предложившего рассмотреть вопрос о прекращении полномочий секретаря студенческого совета НИУ ВШЭ, Быкова Кирилла"""  # Слушали
    session_decision = 'Освободить от должности секретаря Студенческого совета'  # Решили: ...


class VkApi:
    @staticmethod
    def auth():
        """ авторизовывает пользователя и возвращает объект апи """

        vk_session = vk_api.VkApi(Config.login, Config.password)
        try:
            vk_session.auth(token_only=True)
        except vk_api.AuthError as error_msg:
            print(error_msg)
            return

        return vk_session.get_api()

    @staticmethod
    def get_poll(vk: vk_api.vk_api.VkApiMethod, link: str) -> dict:
        """ получает голосование """

        if link.find('wall') != -1:
            post_id = link[link.find('wall') + 4:]
            response = vk.wall.getById(posts=post_id)
            for attachment in response[0]['attachments']:
                if attachment['type'] == 'poll':
                    return attachment['poll']
        elif link.find('poll') != -1:
            post_id = link[link.find('poll') + 4:].split('_')
            response = vk.polls.getById(owner_id=post_id[0], poll_id=post_id[1])
            return response

        else:
            print('Некорректная ссылка')
            return {}

    @staticmethod
    def get_poll_answers(vk: vk_api.vk_api.VkApiMethod, poll: dict) -> dict:
        """ возвращает словарь с ответами на голосование """

        poll_id = poll['id']
        poll_owner_id = poll['owner_id']
        answers = vk.polls.getById(owner_id=poll_owner_id, poll_id=poll_id)
        return answers['answers']

    @staticmethod
    def get_voters(vk: vk_api.vk_api.VkApiMethod, answers: dict, poll: dict):

        poll_id = poll['id']
        poll_owner_id = poll['owner_id']
        voted_dict = {}
        voted = []
        answer_ids = []
        for answer in answers:
            answer_ids.append(str(answer['id']))
            voted.append(answer['text'])
            voted_dict[answer['text']] = []

        voters_resp = vk.polls.getVoters(owner_id=poll_owner_id, poll_id=poll_id, answer_ids=', '.join(answer_ids))

        for voter in voters_resp:
            for i in range(len(answer_ids)):
                if str(voter['answer_id']) == answer_ids[i]:
                    voted_dict[voted[i]] = voter['users']['items']

        return voted_dict

    @staticmethod
    def get_voters_count(voters: list) -> int:
        """ возвращает количество проголосовавших """

        return len(voters)

    @staticmethod
    def make_list_of_weights(voters: list) -> list:
        weights = []
        for voter in voters:
            if str(voter) in SSmembers.weights:
                weights.append(SSmembers.weights[str(voter)])

        return weights

    @staticmethod
    def replace_ids_with_students_names(voters: list) -> list:
        students = []
        for voter in voters:
            if str(voter) in SSmembers.SSmembers:
                students.append(SSmembers.SSmembers[str(voter)].replace(" ", "~"))

        return students


if __name__ == '__main__':
    vk = VkApi.auth()
    poll = VkApi.get_poll(vk, Config.wall_url)
    answers = VkApi.get_poll_answers(vk, poll)
    voters = VkApi.get_voters(vk, answers, poll)
    all_students = []
    current_weight = 0
    vote_text = ''
    # with open("mycsvfile.csv", "w") as outfile:
    #     writer = csv.writer(outfile)
    for student in voters.keys():
        if "рез" in student.lower() or "проголосовал" in student.lower():
            continue
        tmp = [student]
        list_of_weights = VkApi.make_list_of_weights(voters[student])
        # tmp.extend(list_of_weights)
        weight = sum([float(x) for x in list_of_weights])
        current_weight += weight
        tmp.extend(VkApi.replace_ids_with_students_names(voters[student]))
        # print(student, weight, sep=": ")
        if len(tmp) > 1:
            vote_text += student + " - " + f'{weight:.4f}' + " (" + ", ".join(tmp[1:]) + ")\\\\"
            # print(student, "-", weight, " (" + ", ".join(tmp[1:]) + ")\\\\")
        else:
            vote_text += student + " - " + f'{weight:.4f}\\\\'
            # print(student, "-", weight)
        all_students.extend(tmp[1:])
        # writer.writerow(tmp)

    # wb = Workbook()
    # ws = wb.active
    # with open('mycsvfile.csv', 'r') as f:
    #     for row in csv.reader(f):
    #         ws.append(row)
    # wb.save('students.xlsx')
    all_students.sort()
    # print("Кол-во:", len(all_students))
    # print("Суммарный вес:", current_weight)
    # print(", ".join(all_students))

    template_variables = {
        'SESSION_PLACE': Config.session_place,
        'SESSION_NUMBER': Config.session_number,
        'SESSION_DATE': Config.session_date.replace(' ', '~'),
        'SESSION_PEOPLE_COUNT': len(all_students),
        'SESSION_PEOPLE_COUNT_TEXT': num2text(len(all_students)),
        'SESSION_PEOPLE_WEIGHT': f'{current_weight:.4f}',
        'SESSION_MEMBERS': ', '.join(all_students),
        'SESSION_DESCRIPTION': Config.session_description,
        'SESSION_VOTE_DESCRIPTION': Config.session_vote_description,
        'VOTE': vote_text,
        'SESSION_DECISION': Config.session_decision,
        'SUBSCRIPTION_DATE': Config.session_date.upper(),
        'SIGN_PATH': Config.sign_path,
    }    

    LatexMethods.run(template_variables)
    print("Нужно добрать " + str(52361.8752 - current_weight * 2))
    