

# 1) These functions were used to determine the correct conjugation for a verb in its different forms.
def present_simple_conj(subject, verb):
    exceptions_to_rules = ['have', 'be']
    conj_subjects_1, conj_subjects_2 = ['I','you','we','they'], ['he','she','it']
    consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']
    if subject in conj_subjects_1:
        if verb in exceptions_to_rules:
            if verb == exceptions_to_rules[0]:
                pass
            elif verb == exceptions_to_rules[1]:
                if subject == conj_subjects_1[0]:
                    result = 'am'
                elif subject in [conj_subjects_1[1], conj_subjects_1[2], conj_subjects_1[3]]:
                    result = 'are'
        else:
            result = verb
    elif subject in conj_subjects_2:
        if verb in exceptions_to_rules:
            if verb == exceptions_to_rules[0]:
                result = 'has'
            elif verb == exceptions_to_rules[1]:
                result = 'is'
        elif verb[-2] in consonants and verb[-1] == 'y':    #-ies form
            result = f'{verb[0:-1]}ies'
        elif verb[-1] in ['s', 'x', 'o', 'z'] or verb[-2:] in ['sh', 'ch']:  #-es form
            result = f'{verb}es'
        else:
            result = f'{verb}s'
    return result

def ing_conj(ing_double,ing_double_stress,verb):
    cvc1 = ['b','c','d','f','g','h','j','k','l','m','n','p','q','r','s','t','v','w']
    cvc2 = ['a','e','i','o','u']
    cvc3 = cvc1
    if verb[-1] in ['w', 'y', 'x']:
        ing_form = f"{verb}ing"
    elif verb == 'parallel':
        ing_form = "paralleling"
    elif ing_double_stress is True and verb[-1] in cvc1 and verb[-2] in cvc2 and verb[-3] in cvc3:
        ing_form = f"{verb}{verb[-1]}ing"
    elif ing_double_stress is False and ing_double == True and verb[-1] in cvc1 and verb[-2] in cvc2 and verb[-3] in cvc3:
        ing_form = f"{verb}ing"
        if verb[-1] == 'l' and verb[-2] in cvc2:
            ing_form = f"{verb}{verb[-1]}ing,{verb}ing"  #exceptions for the yanks
    elif verb == 'be':
        ing_form = f"{verb}ing"
    elif verb in ['dye', 'singe', 'binge']:   #special exceptions
        ing_form = f"{verb}ing"
    elif verb == 'queue':
        ing_form = "queueing,queuing"
    elif verb == 'quit':
        ing_form = f'{verb}{verb[-1]}ing'  #this is because qu is acting as a 'w' sound
    elif verb[-2:] == 'ie':
        ing_form = f"{verb[0:-2]}ying"
    elif verb[-2:] == 'ee':
        ing_form = f"{verb}ing"
    elif verb[-1] == 'e':
        ing_form = f"{verb[:-1]}ing"
    elif verb[-2:] == 'ic':
        ing_form = f"{verb}king"
    elif verb[-1] in cvc1 and verb[-2] in cvc2 and verb[-3] in cvc3:
        ing_form = f"{verb}{verb[-1]}ing"
    else:
        ing_form = f"{verb}ing"
    return ing_form

# 2) A marking algorithm that utilised a Levenshtein (or character difference) between an ideal string and a student's potential answer string:

import pylev
def question_marker(answer,correct_answer_list,act_type,extra_details):
    '''A new 0.3 function that marks all questions, as well as new questions to give some tolerance to answers.'''
    print(f'ans: {answer}, corr_list: {correct_answer_list},type: {type(correct_answer_list)},act: {act_type},extra: {extra_details}')
    if act_type == 1:#Type 1
        if answer in correct_answer_list:
            answer_correct_var = True
        else:
            answer_correct_var = False
    elif act_type in [2, 11]:     #type 2
        if answer == correct_answer_list:
            answer_correct_var = True
        else:
            answer_correct_var = False
    elif act_type == 3:    #type 3
        if type(answer) == list:
            if answer[0] in correct_answer_list:
                answer_correct_var = True
            else:
                answer_correct_var = False
        else:
            answer_correct_var = True if answer in correct_answer_list else False
    elif act_type == 4:
        try:
            correct_answer_list = correct_answer_list.split(',')
        except AttributeError:
            pass
        if extra_details == 1:  #one answer
            if answer.lower() in correct_answer_list:
                answer_correct_var = True
            else:
                answer_correct_var = False
        elif extra_details == 2: #multi answer
            if answer[0].lower() and answer[1].lower() in correct_answer_list:
                answer_correct_var = True
            else:
                answer_correct_var = False
            if answer_correct_var is True:
                if len(correct_answer_list) == 2:
                    if answer[0].lower() == correct_answer_list[0] and answer[1].lower() == correct_answer_list[1]:
                        answer_correct_var = True
                    else:
                        answer_correct_var = False
        # for potential_answer in correct_answer_list: (maybe not yet)
        #     lev_distance = Levenshtein.distance(potential_answer,answer)
        #     print(f'lev_distance: {lev_distance}')
        #     if lev_distance <= 2:
        #         answer_correct_var = True
        #         break
        #     else:
        #         answer_correct_var = False
    elif act_type == 7 or act_type == 10:
        if extra_details == '':
            if answer == correct_answer_list:
                answer_correct_var = True
            else:
                answer_correct_var = False
        elif extra_details == 'sa':
            if type(correct_answer_list) == list:
                if len(correct_answer_list) == 1:
                    lev_distance = pylev.levenshtein(answer.lower(), correct_answer_list[0].lower())
                    if lev_distance <= 2:
                        answer_correct_var = True
                    else:
                        answer_correct_var = False
                else:
                    correct_var = False
                    for item in correct_answer_list:
                        lev_distance = pylev.levenshtein(answer.lower(), item.lower())
                        if lev_distance <= 2:
                            correct_var = True
                        else:
                            pass
                    if correct_var == True:
                        answer_correct_var = True
                    else:
                        answer_correct_var = False
            else:
                lev_distance = pylev.levenshtein(answer.lower(),correct_answer_list.lower())
                if lev_distance <= 2:
                    answer_correct_var = True
                else:
                    answer_correct_var = False
            print(f'lev_distance: {lev_distance}')

    #type 4

    #type 5

    #type 6

    #type 7

    #type 8

    #type 9

    #type 10
    pass
    if answer_correct_var == True:
        print('The answer is correct!')
    else:
        print('The answer is incorrect!')
    return answer_correct_var


# 3) The algorithm that drove custom text appearing to the user in the main screen, helping them to understand how far they've come and providing them encouragement in different areas

wrong_stuff = {}
def private_teacher_speaks(init_login,percent_accuracy):
    '''Provides Private Teacher with some sentences to show the user.'''
    #core variables
    strip1 = percent_accuracy.strip('[b]')
    strip2 = strip1.strip('[/b]')
    raw_accuracy_number = strip2.strip('%')

    print(f'private teacher speaks percent accuracy= {raw_accuracy_number}')
    if raw_accuracy_number == '':
        average_accuracy = '-'
        t_comment = ''
    else:
        average_accuracy = raw_accuracy_number
        t_comment = user_gradercomment(raw_accuracy_number)
    name = user_main_vars['u_user_name'].title()
    greeting = update_greeting()
    time = strftime('%H')
    u_time = user_main_vars['u_total_time']
    day_of_week = strftime('%A')

    #get time of day word
    if 0 <= int(time) < 12:
        time_of_day = 'morning'
    elif 12 <= int(time) < 17:
        time_of_day = 'afternoon'
    elif 17 <= int(time) < 20:
        time_of_day = 'evening'
    elif 20 <= int(time) < 24:
        time_of_day = 'night'

    #get appropriate question from time of day word and mix it with random greetings
    greeting_list = ['are things','are things going','is everything','is it going',]
    if time_of_day == 'morning':
        day_tense = 'are you this morning'
    elif time_of_day == 'day':
        day_tense = 'is your day'
    elif time_of_day == 'afternoon' or time_of_day == 'evening':
        day_tense = 'has your day been'
    elif time_of_day == 'night':
        day_tense = 'was your day'

    greeting_option = random.choice([random.choice(greeting_list),day_tense])
    ref_press = 0
    if init_login == 0:
        #Private Teacher will provide these greetings upon startup.
        init_login_list = [f"{greeting}, {name}. Hope you're having a nice {time_of_day}.", f"{greeting}, {name}. How {greeting_option}?"]
        if day_of_week == 'Monday':
            day_greeting = random.choice([f'Just another manic Monday, {name}. Hope you have a good week!', f"It's Monday, {name}. Hope you had a nice weekend."])
        elif day_of_week == 'Tuesday':
            day_greeting = random.choice([f'There are over 65 songs about Tuesday, {name}. Have a listen to some!', f'{name}, Tuesday can be hard for some people. It is pronounced choose-day.'])
        elif day_of_week == 'Wednesday':
            day_greeting = random.choice([f'Hump day is here! Happy Wednesday, {name}!', f'Did you know that Wednesday was named after the Anglo-Saxon god Wodan, {name}?'])
        elif day_of_week == 'Thursday':
            day_greeting = random.choice([f'Over the hump now. Happy Thursday, {name}.', f'{name}, did you know that Thursday was named after the Viking god Thor?'])
        elif day_of_week == 'Friday':
            day_greeting = random.choice([f"TGIF, {name}! (Thank God It's Friday)",f"It's Friday, {name}! The weekend is just around the corner."])
        elif day_of_week in ['Saturday', 'Sunday']:
            day_greeting = random.choice([f"It's finally the weekend, {name}! Got any plans?", f"The weekend is here, {name}! Time to relax (or study more?)"])
        init_login_list.append(day_greeting)
        sentence = random.choice(init_login_list)

    elif init_login == 1:
        try:
            if len(u_completed_activities) == 0:
                # Private Teacher will say these things when the user has done nothing:
                zero_done_list = [f'Hey {name}, complete some activities so Private Teacher can provide you with feedback!', \
                                  f'{name}, activities are the heart of Private Teacher. I recommend starting with [ref="conjugators"][b][u]the conjugators.[/u][/b][/ref]']
                sentence = random.choice(zero_done_list)
                ref_press = 1
            elif len(u_completed_activities) == 1:
                # Private teacher will say these things when the user has done one activity.
                one_done_list = [f'Congratulations on finishing your first activity! {t_comment.lower()} You can see the answers inside [ref="portfolio"][b][u]your portfolio.[/u][/b][/ref]',\
                                 f'Your first activity is completed! Take a look at your [ref="score"][b][u]updated gScore.[/u][/b][/ref]',\
                                 f'You have taken your first step. One activity completed!']
                sentence = random.choice(one_done_list)
                ref_press = 2 if sentence == one_done_list[0] else 3
            elif 3 <= len(u_completed_activities) < 6:
                # after three activities:
                three_done_list = [f"Congratulations on {len(u_completed_activities)} activities completed, {name}! You have averaged, so far, {average_accuracy}% accuracy from all your results. {t_comment}",\
                                   f"Nice! Now you have completed {len(u_completed_activities)} activities, spending {int(u_time/60)} minutes in this app! - They say it takes 10,000 hours to master something!",
                                   f"As you have completed {len(u_completed_activities)} activities, you can now access your [ref='analysis'][b][u]analysis![/u][/b][/ref]"]
                sentence = random.choice(three_done_list)
                ref_press = 4
            elif 10 <= len(u_completed_activities) <= 50:
                random_number = random.choice([1,2])
                if random_number == 1:
                    skills_dict = {'listening': skill_score_get('l'), 'reading': skill_score_get('r'), 'speaking': skill_score_get('s'),
                                   'writing': skill_score_get('w'), 'grammar/vocabulary': skill_score_get('gv')}
                    skills_list = []
                    skills_to_improve = []
                    for skill, score in skills_dict.items():
                        skills_list.append(score)
                    worst_skill = min(skills_list)
                    worst_skill_counter = 0
                    for skill, score in skills_dict.items():
                        if score == worst_skill:
                            worst_skill_counter += 1
                    if worst_skill_counter == 1:
                        for skill, score in skills_dict.items():
                            if score == worst_skill:
                                skill_to_improve = skill
                    else:
                        for skill, score in skills_dict.items():
                            if score == worst_skill:
                                skills_to_improve.append(skill)
                    if worst_skill_counter == 1:
                        ten_done_bad_skill = f"{len(u_completed_activities)} activities completed! But remember, don't neglect your {skill_to_improve} skills!"
                    elif worst_skill_counter > 1:
                        joint_skills = ', '.join(skills_to_improve)
                        ten_done_bad_skill = f"{len(u_completed_activities)} activities completed! But remember, don't neglect your skills in {joint_skills}!"

                    ten_done_list = [f'You have now completed {len(u_completed_activities)} activities! Private Teacher can [ref="guess"][b][u]guess your level[/u][/b][/ref] after you have achieved 3 silver stars in activities.',
                                     ten_done_bad_skill,]
                    sentence = random.choice(ten_done_list)
                    ref_press = 5
                elif random_number == 2:
                    if len(wrong_stuff.keys()) == 0:
                        conj_activities = [x for x in activities.values() if 'conj_' in x]
                        for k,v in u_completed_activities.items():
                            print(k[10:])
                            if k[10:] in conj_activities:
                                for k2,v2 in v.items():
                                    if k2 != 0:
                                        chosen, correct = v2['chosen_answer'], v2['correct_answer']
                                        chosen_list, correct_list = chosen.split(','), correct.split(',')
                                        if question_marker(chosen_list[0], correct_list, 1, '') is False:
                                            try:
                                                wrong_stuff[k[10:]] = [chosen, correct]
                                            except:
                                                pass
                    random_tense = random.choice(list(wrong_stuff))
                    random_question_pair = wrong_stuff[random_tense]
                    sentence_1_randomness = random.choice(['Remember',"Don't forget", "Keep this in mind"])
                    sentence = f'{sentence_1_randomness} {name}, the correct conjugation is {random_question_pair[1]}, not {random_question_pair[0]}! [ref="rules"][b][u]Check the rules[/u][/b][/ref] if you need some help!'
                    ref_press = 6
                else:
                    sentence = f"You have completed {len(u_completed_activities)} activities. Your average accuracy is {average_accuracy}%."
            else:
                sentence = f"You have completed {len(u_completed_activities)} activities. Your average accuracy is {average_accuracy}%."
        except Exception as e:
            print(e)
            sentence = f"You have completed {len(u_completed_activities)} activities. Your average accuracy is {average_accuracy}%."
            ref_press = 1
    return [sentence, ref_press]
