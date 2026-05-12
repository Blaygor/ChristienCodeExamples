# An as-is look at how I debugged and implemented a working calendar that would show live updates of booked times with teachers. The calendar could be clicked on and entries made to it in real time. Looking back now I would've utilised classes and inheritance a whole lot more here (instead of messy dictionary management)

#code to do with the calendar functionality on the websites.
import urllib
# from market.routes import main_lesson_hours   #as a list with start and end date
from market.languages import language_dict
from market.global_assets import lang_cookie_check
main_lesson_hours = [7, 22]
timetable_route_address = 'http://127.0.0.1:5000/timetable?'
selected_event = ''
selected_lesson = ''
datetime_template = "%Y-%m-%d %H:%M:%S.%f"


from market import user_prefs
from datetime import datetime as dt
from datetime import timedelta
from datetime import date
# from colorama import Fore, Back, Style
# from market.routes import no_col, g, r, b, gfi_fn

def suffix_code(number):
    '''Determines the suffix code for the date.'''
    try:
        number_int = int(number)
        # print(f'The number{number_int}')
        if 4 <= number_int <= 20 or 24 <= number_int <= 30:  # setting date correctly.
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][number_int % 10 - 1]
        return f'{number_int}{suffix}'
    except Exception as e:
        return number

def calendar_events_to_utc(teacher_calendar_events, event_gmt_time, time_to_change_to):
    '''1. Takes a teacher calendar events and converts it to UTC. 2. Changes a UTC calendar into GMT+-.'''
    # print(f'INCOMING TO FN TEACHER CALENDAR EVENTS: {teacher_calendar_events}')
    # 1. Makes a copy of the incoming calendar events.
    import copy
    precalc_events_tocopy = copy.deepcopy(teacher_calendar_events)

    # 2. Initialising a table and a dictionary to store calculated values.
    events_timezone_adjusted = []
    availability_roster = {}  # in format 'date':[hour strings]

    # 3. Loops through each event in the incoming calendar events (should be ~30 in total).
    loop_counter = 0
    for event_dict in teacher_calendar_events:  # each event is a dictionary.
        # print(f'PRINTING EVENT_DICT: {event_dict}')
        # for k, v in event_dict.items():

        # 3a. Extracts start time, end time variables to modify. Changes them to a string.
        start_time = event_dict['start']  # in formats 2022-01-11T10:00:00
        end_time = event_dict['end']

        # 3b. Changes them to a string.
        #TODO TRIED CHANGING THIS.... from 5 0 to 6 0
        start_time_in_string = f'{start_time[0:10]} {start_time[11:]}.000000'
        end_time_in_string = f'{end_time[0:10]} {end_time[11:]}.000000'
        # print(f'START TIME IN STRING: {start_time_in_string} ')

        # 3c. Determines whether change should go into UTC time, or GMT adjusted time.
        # 3d. Makes adjustment by sending strings into add_subtract_utc, then formatting the string for the calendar.
        start_time_in_string_adjusted = add_subtract_utc(start_time_in_string, event_gmt_time, time_to_change_to)
        # print(f'START TIME IN STRING ADJUSTED: {start_time_in_string_adjusted} for id {event_dict["id"]}')
        start_time_in_string_reformatted = f'{start_time_in_string_adjusted[:10]}T{start_time_in_string_adjusted[11:16]}'
        end_time_in_string_adjusted = add_subtract_utc(end_time_in_string, event_gmt_time, time_to_change_to)
        end_time_in_string_reformatted = f'{end_time_in_string_adjusted[:10]}T{end_time_in_string_adjusted[11:16]}'

        # 3e. Modifies the copied dictionary, replacing the start and end times with the reformatted strings.
        precalc_events_tocopy[loop_counter]['start'] = start_time_in_string_reformatted
        precalc_events_tocopy[loop_counter]['end'] = end_time_in_string_reformatted
        # print(f'PRECALCULATED_EVENTS_ORIGINAL_START: {precalc_events_tocopy[loop_counter]["start"]}')
        # print(f'PRECALCULATED_EVENTS_ORIGINAL_end: {precalc_events_tocopy[loop_counter]["end"]}')
        loop_counter += 1

    # 4. Return the updated calendar back to routes.
    return precalc_events_tocopy

def hour_to_float(number):
    '''Converts a float to hour.'''
        #Number s hould be a full time string. "%Y-%m-%d %H:%M:%S.%f" "yyyy-mm-dd
    if number[14:16] != '00':
        if number[14:16] == '15':
            x = 0.25
        elif number[14:16] == '30':
            x = 0.5
        elif number[14:16] == '45':
            x = 0.75
    else:
        x = 0
    return float(int(number[11:13])) + x


def set_opening_hours_utc_adjusted(opening_hours, teacher_time_zone, new_time_zone, just_opening_hours):
    '''Takes a set of default opening hours for each teacher and converts them, also sending back an dictionary that can be used to build the calendar.'''
    # Take opening hours and convert them to the timezone.
    #PART 1:  COnvert to UTC
    #List in format [7,22] start time and end time.
    global main_lesson_hours
    # print(f'MAIN OPENING HOURS PRE-SET: {main_lesson_hours}')
    main_lesson_hours = opening_hours  #set main_lesson_hours
    # print(f'MAIN OPENING HOURS POST-SET: {main_lesson_hours}')


    #turn these into two fictional times on the same day.
    utc_string_1 = convert_user_hours_to_utcstring('2022-06-12', opening_hours[0])
    utc_string_2 = convert_user_hours_to_utcstring('2022-06-12', opening_hours[1])
    # print(f'PRINTING UTC STRINGS: {utc_string_1}, {utc_string_2} + time zone {new_time_zone}')

    #turn them into datetime objects.
    utc_string_1_obj = dt.strptime(utc_string_1, datetime_template)
    utc_string_2_obj = dt.strptime(utc_string_2, datetime_template)

    #timedelta the datetime objects.
    time_modify = timezone_hours_to_modify(teacher_time_zone)
    if teacher_time_zone[3] == '+':
        datetime_morphed_1 = utc_string_1_obj - timedelta(hours=time_modify)
        datetime_morphed_2 = utc_string_2_obj - timedelta(hours=time_modify)
    elif teacher_time_zone[3] == '-':
        datetime_morphed_1 = utc_string_1_obj + timedelta(hours=time_modify)
        datetime_morphed_2 = utc_string_2_obj + timedelta(hours=time_modify)
    #PART 2: Convert over to the new timecode.
    new_opening_hours = []
    if new_time_zone != 'GMT':
        time_modify = timezone_hours_to_modify(new_time_zone)
        # print(f'TIME MODIFYHYYYYYYY: {time_modify}')
        if new_time_zone[3] == '+':
            datetime_morphed_3 = datetime_morphed_1 + timedelta(hours=time_modify)
            datetime_morphed_4 = datetime_morphed_2 + timedelta(hours=time_modify)
            # print(f'DATETIEM MORPHED 3+4 if {datetime_morphed_3, datetime_morphed_4}')
        elif new_time_zone[3] == '-':
            datetime_morphed_3 = datetime_morphed_1 - timedelta(hours=time_modify)
            datetime_morphed_4 = datetime_morphed_2 - timedelta(hours=time_modify)
            # print(f'DATETIEM MORPHED 3+4 else {datetime_morphed_3, datetime_morphed_4}')
        back_to_string_1 = dt.strftime(datetime_morphed_3, datetime_template)  # [11:13]
        back_to_string_2 = dt.strftime(datetime_morphed_4, datetime_template)  # [11:13]
    #string operations to get the MODIFIED time back
    else:
        back_to_string_1 = dt.strftime(datetime_morphed_1, datetime_template)#[11:13]
        back_to_string_2 = dt.strftime(datetime_morphed_2, datetime_template)#[11:13]
    # print(f'backtostring: {back_to_string_1, back_to_string_2}')
    final_time_1 = hour_to_float(back_to_string_1)
    final_time_2 = hour_to_float(back_to_string_2)
    # print(f"FFFFFFFFFFFFFFFFFFFFFFFFFFinal time 1:2: {final_time_1} {final_time_2}")
    new_opening_hours = [final_time_1, final_time_2]
    if just_opening_hours is True:
        return new_opening_hours
    # new_opening_hours_timestring = convert_user_hours_to_utcstring(back_to_string_1[:10])
    if new_opening_hours[1] > new_opening_hours[0]: #good news! No modification needed.
        dict_entry = {'daysOfWeek': [0, 1, 2, 3, 4, 5, 6],
                  'startTime': f'{back_to_string_1[11:16]}',
                  'endTime': f'{back_to_string_2[11:16]}',
                  }
        print(f'NEW OPENING HOURS:{new_opening_hours}, DICT: {dict_entry}')
        return [new_opening_hours, [dict_entry]]
        # print(f'RETURNED {[new_opening_hours, dict_entry]} from default if ')
    else:   #modification needed
        #first hour is an evening hour
        #We need to make two dictionaries dealing with this issue. both take all days of the week.

        #for time 1, We need to create an event starting at time 1 and finishing at 24:00.

        #for time 2, We need to create an event starting at 0 and finishing at time 1.

        dict_entry_1 = {'daysOfWeek': [0, 1, 2, 3, 4, 5, 6],   #morning time
                        'startTime': '00:00', #midnight
                        'endTime': back_to_string_2[11:16]} #morning finish time
        dict_entry_2 = {'daysOfWeek': [0, 1, 2, 3, 4, 5, 6],  #evening time
                        'startTime': back_to_string_1[11:16],
                        'endTime': '24:00'} #midnight
        dict_to_return = [dict_entry_1,dict_entry_2]
        return [new_opening_hours, dict_to_return]
    print(f'NEW OPENING HOURS:{new_opening_hours}')
    return new_opening_hours


    # new_opening_hours.append[dt.strftime(datetime_morphed_1, datetime_template )[11:13],dt.strftime(datetime_morphed_2, datetime_template )[11:13]]

    #get adjustment factor with time_zone
def timezone_hours_to_modify(timezone):
    '''Gets timezone hour modifiers from a timezone.'''
    if ':' in timezone: #fractional time
        gmt_var = timezone[4:]
        colon_position = gmt_var.find(':')
        time_fraction = gmt_var[colon_position + 1:]
        whole_hour = float(gmt_var[:colon_position])
        if time_fraction == '15':
            x = .25
        elif time_fraction == '30':
            x = .5
        elif time_fraction == '45':
            x = .75
        time_modify = whole_hour + x
    else:
        try:
            time_modify = int(timezone[4:])
        except ValueError:
            time_modify = '' #GMT time
    return time_modify


def add_subtract_utc(time_variable, old_time_zone, new_time_zone):
    '''Changing from UTC to UTC+, UTC-. Needs format yyyy-mm-dd hh:mm:ss.00000 either in datetime or string.'''
    # print(f'ADD SUBTRACTTTTTTT UTC VARS: {time_variable, old_time_zone, new_time_zone}')
    def back_to_utc(gmt_object):
        '''reverts the time to base UTC.'''
        if old_time_zone[3] == '+':
            datetime_morphed = gmt_object - timedelta(hours=time_modify_old)
        elif old_time_zone[3] == '-':
            datetime_morphed = gmt_object + timedelta(hours=time_modify_old)
        return datetime_morphed

    def calculate_from_utc(base_utc_object):
        '''Makes the time calculation from the base UTC that was calculated before.'''
        if new_time_zone[3] == '+':
            datetime_morphed = base_utc_object + timedelta(hours=time_modify_new)
        elif new_time_zone[3] == '-':
            datetime_morphed = base_utc_object - timedelta(hours=time_modify_new)
        return datetime_morphed

    # 1. Prepare 2 variables to use timedelta. GMT+10:30 will change to 10.5, GMT to GMT, -10 to 10
    time_modify_old = timezone_hours_to_modify(old_time_zone)
    time_modify_new = timezone_hours_to_modify(new_time_zone)
    # print(f'time modify old {time_modify_old} time modify new {time_modify_new}')

    # 2. Perform a check to make sure that the data to use with Timedelta is a datetime object. Convert if not.
    # print(f'HERE IS TIME VARIABLE: {time_variable}')
    #exception for 24
    if time_variable[11:13] == '24':
       time_variable = dt.strptime(f'{time_variable[:10]} 00{time_variable[13:]}', "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=24)
    try:
        time_variable_obj = time_variable if isinstance(time_variable, dt) else dt.strptime(time_variable, datetime_template)
    except ValueError: #Coming from the calendar
        try:
            time_variable_obj = time_variable if isinstance(time_variable, dt) else dt.strptime(time_variable, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                time_variable_obj = time_variable if isinstance(time_variable, dt) else dt.strptime(time_variable, "%Y-%m-%d %H:%M.%f")
            except:
                time_variable_obj = time_variable if isinstance(time_variable, dt) else dt.strptime(time_variable, "%Y-%m-%d %H:%M:%S.%f")
    # 3. No changes needed if the new timezone is equal to the old timezone.
    if new_time_zone == old_time_zone:
        # print('doing nothing...')
        return time_variable #

    # 4. If the old time zone is GMT and the new time zone isn't GMT, Convert straight to GMT+/- :
    elif old_time_zone == 'GMT' and new_time_zone != 'GMT':
        # print(f'Choice 2')
        datetime_morphed = calculate_from_utc(time_variable_obj)
        # print(f'DATETIME MORPHED INTO: {datetime_morphed} ')

    # 5. If the old time zone isn't GMT, trigger this block.
    elif old_time_zone != 'GMT':
        # print(f'Choice 3')

        # 5a. Convert back to GMT.
        datetime_morphed_temp = back_to_utc(time_variable_obj)
        # print(f'DATETIME_MORPHED_TEMP = {datetime_morphed_temp}')

        # 5b. Add or subtract GMT times from the datetime object.
        if new_time_zone != 'GMT':
            # print(f'Choice 4')
            datetime_morphed = calculate_from_utc(datetime_morphed_temp)
            # print(f'DATETIME_MORPHED = {datetime_morphed}')

        # 5c. Keep the temp variable if the New timezone is GMT.
        else:
            # print(f'Choice 5')
            datetime_morphed = datetime_morphed_temp

    # 6. Return the modified time as a string.
    # print(f'returning!!!! {dt.strftime(datetime_morphed, datetime_template)}')
    return dt.strftime(datetime_morphed, datetime_template)

def return_to_utc(start_hour_pre_datetime,end_hour_pre_datetime,time_zone):
    '''Does the addition and subtraction of datetime strings, and outputs in teacher timetable hours.'''
    morphed_hours = []
    for i in ['start', 'end']:
        hour_to_modify = start_hour_pre_datetime if i == 'start' else end_hour_pre_datetime
        # run the function add_subtract_utc(start_hour_pre_datetime,end_hour_pre_datetime
        datetime_object = dt.strptime(hour_to_modify, datetime_template)
        time_modify = timezone_hours_to_modify(time_zone)
        try:
            if time_zone[3] == '+':
                datetime_morphed = datetime_object - timedelta(hours=int(time_modify))
            elif time_zone[3] == '-':
                datetime_morphed = datetime_object + timedelta(hours=int(time_modify))
        except Exception:  # GMT time
            datetime_morphed = datetime_object

        morphed_hour_string = dt.strftime(datetime_morphed, datetime_template)
        morphed_hours.append(morphed_hour_string)  # into a new day and hour
    return morphed_hours


def convert_name_timetable_to_utc(teacher_name, initial_availabilities_1_teacher, outgoing_gmt_code, incoming_gmt_code):
    '''Converts a complete timetable of teacher x for the timetable {'date': [[y,z],[a,b]]} into a UTC adjusted one.'''

    # 1. Start up a dictionary with the teacher's name. This will be filled in below.
    utc_converted_dates = {teacher_name: {}}

    # 2. Loop through the availabilities for this teacher, going by each date.
    for date, hours_taken in initial_availabilities_1_teacher.items():
        # 2a. If there is nothing in the day, skip process.
        if len(hours_taken) == 0:
            try:
                if len(utc_converted_dates[teacher_name][date]) == 0:
                    utc_converted_dates[teacher_name][date] = hours_taken
                else:
                    pass
            except KeyError:
                utc_converted_dates[teacher_name][date] = hours_taken
        # 2b. If there is something in the day, round the times.
        else:
            # print(f'UTC_LESSON_DAY IN: {date, hours_taken, outgoing_gmt_code}')
            utc_lesson_day = lesson_list_to_utc(date, hours_taken, outgoing_gmt_code, incoming_gmt_code) #lessons taken in go to UTC time.
            # print(f'UTC_LESSON_DAY REEEEEEEEEEEEEEEEEEEEEE: {utc_lesson_day}')
            for date, time_blocks in utc_lesson_day.items():
                # print(f'WHY NO WORK: {utc_converted_dates[teacher_name].keys()}')
                try:
                    if date in utc_converted_dates[teacher_name].keys(): #Add any dates together.
                        # print(f'1TIME BLOCK: {time_blocks}')
                        utc_converted_dates[teacher_name][date].append([time_blocks[0][0],time_blocks[0][1]])
                        # print(f'2found date!')
                    else:
                        # print(f'MY TIME BLOCKS: {time_blocks}')
                        # print(f'3didn"t find date. Creating... {date}')
                        utc_converted_dates[teacher_name][date] = time_blocks
                except IndexError as e:
                    if date in utc_converted_dates[teacher_name].keys(): #Add any dates together.
                        # print(f'4TIME BLOCK: {time_blocks}')
                        utc_converted_dates[teacher_name][date].append([time_blocks[0][0]])
                        # print(f'5found date!')
                    else:
                        # print(f'6didn"t find date. Creating... {date}')
                        # print(f'MY TIME BLOCKS: {time_blocks}')
                        utc_converted_dates[teacher_name][date] = time_blocks
    # print(f'UTC CONVERTED DATES READY TO BE RETURNED: {utc_converted_dates}')
    return utc_converted_dates



def get_last_sunday(calculate_month_ahead):
    '''Gets the last sunday to use for display of the calendar, also optionally returns a month in advance.'''
    todays_date, sunday_date = date.today(), None
    todays_day = dt.strftime(todays_date, f"%A")
    for i in range(1, 8): #7 day week range.
        if todays_day == 'Sunday':  #if our date is already sunday...
            sunday_date = todays_date
        else: #if it's not...
            date_temp = todays_date - timedelta(days=i)
            if dt.strftime(date_temp, f"%A") == 'Sunday':
                sunday_date = date_temp
    return sunday_date if calculate_month_ahead is False else todays_date + timedelta(weeks=4)


def timetable_string_modify_time(object, time_in_minutes):
    '''Modifies a timetable datetime object by increasing or decreasing hours.'''
    # print(f'Object IN string_modify_time fn: {object} {type(object)} with time in mins: {time_in_minutes}')
    if time_in_minutes > 0: #adding minutes
        object_modified = object + timedelta(minutes=time_in_minutes)
    elif time_in_minutes < 0: #subtracting minutes
        object_modified = object - timedelta(minutes=abs(time_in_minutes))
    else:
        object_modified = object
    # print(f'MODIFIED OBJECT: {object_modified}')
    return object_modified

def convert_timetable_string_to_datetime(string, new_timezone, old_timezone):
    '''converts a timestable string to datetime: '2022-02-01T07:00:00'''
    #"%Y-%m-%d %H:%M:%S.%f"
    # print(f'STRING IN convert_timetable fn: {string}')
    year = string[:10]
    hour = string[-8:-6]
    minute = string[-5:-3]
    make_to_datetime = f"{year} {hour}:{minute}:00.00000"
    # print(f'MAKE TO DATETIME: {make_to_datetime}')
    if type(old_timezone) is int:  #modifying string
        # print('ping 3')
        try:
            object = dt.strptime(make_to_datetime, datetime_template)
        except ValueError:  #TODO Strange bug that is now fixed?
            object = dt.strptime(f'{year} {string[11:13]}:{string[11:13]}:00.00000', datetime_template)
        modified_object = timetable_string_modify_time(object, old_timezone)  #time object minused time
        # print(f'THE RETURNED MODIFIED OBJECT {modified_object} {type(modified_object)}')
        return modified_object
    else:
        return add_subtract_utc(make_to_datetime, new_timezone, old_timezone)

def cando_moretime(selected_event,calendar_events):
    '''Returns a bool variable if the student is able to select more than the default 1h.'''
    list_number, event_loop_counter = 0, 0  #Event loop counter increasxinWe start with a list number and an event loop numbe
    lang = int(lang_cookie_check())
    print(f'COOKIES SELECTED EVENT: {selected_event}')
    print(f'LEN CALENDAR EVENTS: {len(calendar_events)}')
    try:
        print(f'CANDO MORE TIME INPUTS: {selected_event, calendar_events[1]}')
        for event in calendar_events:
            event_loop_counter += 1
            for event_param, param_val in event.items():
                if event_param == 'id':
                    if selected_event[:13] == param_val[:13]:
                        print('bong')
                        list_number += event_loop_counter
        if calendar_events[list_number]['title'] == language_dict['timetable']['available'][lang] and calendar_events[list_number]['id'][8:10] == calendar_events[list_number - 1]['id'][8:10]:
            print(f'1: {calendar_events[list_number]["id"][8:10]}')
            print(f'2: {calendar_events[list_number - 1]["id"][8:10]}')
            print(f'CANDO MORE TIME HAS FOUND')
            return 'true'
        else:
            return 'false'
    except Exception as e: #catch all baby
        print(f'exception in cando_moretime catchall: {Exception}')
        return 'true'


def lesson_blocks_into_days(lesson_block):
    '''Creates less'''
    ...

def round_all_calendar_times(time_details, time_details_temp, single_time_block_or_full):
    '''Takes a calendar and rounds all times down or up to the hour, so the calendar can function'''
    def make_1_pass(time_0, time_1):
        '''Makes a single pass of the routing function.'''
        # print(f'1 pass time details: {time_0, time_1}')
        start_time, end_time = time_0, time_1
        # duration = end_time - start_time  # to use down the line
        new_end_time = int(end_time) + 1 if type(end_time) is float else end_time
        new_start_time = int(start_time) if type(start_time) is float else start_time
        return [new_start_time, new_end_time]
    # print(f'TIME DETAILS IN ROUND ALL CALLLLLLLLLLLLLLLLLLLLLLLLL {time_details}')

    # 1. Checks if the times given for a day have some unavailabilities. If not, skip.
    if len(time_details) != 0:
        if single_time_block_or_full == 'single':
            # print(f'returning single rounded down: {make_1_pass(time_details[0], time_details[1])}')
            return make_1_pass(time_details[0], time_details[1])

        elif single_time_block_or_full == 'full':
            for class_date, times in time_details.items():  # converts UTC time to UTC adjusted yyyy-mm-dd: [x,y,z] list
                new_times_list_rounded = []
                for time in times:  # for each time block
                    new_times_list_rounded.append(make_1_pass(time[0],time[1]))
            #     start_time, end_time = time[0], time[1]
            #     # duration = end_time - start_time  # to use down the line
            #     new_end_time = int(end_time) + 1 if type(end_time) is float else end_time
            #     new_start_time = int(start_time) if type(start_time) is float else start_time
            #     new_times_list_rounded.append([new_start_time, new_end_time])
            # # print(f'NEW TIMES LIST ROUNDED: {new_times_list_rounded}')
            time_details_temp.update({class_date: new_times_list_rounded})  # replaces old values with rounded

    return time_details_temp

def lesson_list_to_utc(incoming_date, incoming_times_of_day, outgoing_gmt_code, final_conversion): #as complete day lists.
    '''Creates unavailabilities in UTC time from Specified time (default: GMT+11). Primarily, will convert GMT+11 into UTC. Converts a yyyy-mm-dd: [x,y,z] on a hour-by-hour basis.'''
    date_utc_corrected = {}
    # print(f'VARS INTO LESSON LIST TO UTC:{incoming_date, incoming_times_of_day, outgoing_gmt_code, final_conversion}')
    # print(f'INCOMING TIMES OF DAY: {incoming_times_of_day}')
    # print(f"TIME ZONE: {time_zone}")
    for time_block in incoming_times_of_day:
        #Convert incoming date into UTC. > i.e. 2022-01-01, 8
        # print(f'Incoming date: {incoming_date} and Incoming time of day: {time_block}')
        # convert the times to datetime:
        start_hour_pre_datetime = convert_user_hours_to_utcstring(incoming_date, time_block[0],) #in format yyyy-dd-mm 00:00:00.00000
        end_hour_pre_datetime = convert_user_hours_to_utcstring(incoming_date, time_block[1],)
        # print(f'START AND END HOURS: {start_hour_pre_datetime, end_hour_pre_datetime }')
        morphed_hours = return_to_utc(start_hour_pre_datetime, end_hour_pre_datetime, outgoing_gmt_code) #gets back to UTC.
        # print(f'THE RETURNED MORPHED HOURS in UTC: {morphed_hours}')
        if 'GMT+' in final_conversion or 'GMT-' in final_conversion : #Does another conversion over to desired time from UTC.
            # print('gmt triggered!')
            # pass #alreeady eturned to GMT
            morphed_hours = [add_subtract_utc(start_hour_pre_datetime, outgoing_gmt_code, final_conversion),
                             add_subtract_utc(end_hour_pre_datetime, outgoing_gmt_code, final_conversion)]
            # print(f'Just testing: {add_subtract_utc(morphed_hours[0], "GMT+11", "GMT+1")} | {add_subtract_utc(morphed_hours[1], "GMT+11", "GMT-12")}')
        elif 'round' in final_conversion:  #and outgoing_gmt_code == 'GMT+11':
            # print('round triggered!')
            morphed_hours = [start_hour_pre_datetime, #TODO: FURTHER OPTIMISATION NEEDED
                             end_hour_pre_datetime]
            # print(f'IMMINENT MORPHED {morphed_hours}')
        elif final_conversion is None:
            # print('none triggered!')
            pass #do nothing extra
        # print(f'MORPHED HOURS: {morphed_hours}')
        index = morphed_hours[0].index(':')
        # print(f'INDEX: {index}')
        #surgery needs to be performed.
        #now they need to go back to original format
        new_date_1 = morphed_hours[0][:10]
        new_date_2 = morphed_hours[1][:10]
        # print(f'NEW MORPHED HOURS: {morphed_hours[0]} {morphed_hours[1]}')
        #start_time
        index = morphed_hours[0].index(':')
        try: #single digit hour
            # print(1)
            if morphed_hours[0][-2:index][0] == '':
                # print(2)
                morphed_hours[0][index-2] == '0'
        except IndexError: #multi-digit hour
            # print(3)
            # print('fag')
            if morphed_hours[0][index+1:index+3] == '00': #is it on the hour
                temp_var = int(morphed_hours[0][index-2:index])
                # print(4)
                # print(f"4'S TEMP VAR: {temp_var} ")
                # print('ping')
            else:
                # print(5)
                if morphed_hours[0][index+1:index+3] == '15':
                    # print(6)
                    temp_var = float(morphed_hours[0][index-2:index]) + 0.25
                    # print('ping2')
                elif morphed_hours[0][index+1:index+3] == '30':
                    print(7)
                    temp_var = float(morphed_hours[0][index-2:index]) + 0.50
                    # print('ping3')
                elif morphed_hours[0][index+1:index+3] == '45':
                    print(8)
                    temp_var = float(morphed_hours[0][index-2:index]) + 0.75
                    # print('ping4')
        utc_new_start = temp_var
        # end_time
        index = morphed_hours[1].index(':')
        try:
            # print(9)
            if morphed_hours[1][-2:index][0] == '':
                # print(10)
                morphed_hours[1][index-2] == '0'
        except IndexError:
            # print('dong')
            # print(11)
            if morphed_hours[1][index+1:index+3] == '00': #is it on the hour
                # print(12)
                temp_var = int(morphed_hours[1][index-2:index])
                # print(f"12's TEMP VAR: {temp_var}")
                # print('pingspecial')
            else:
                # print(13)
                # print(f'INDEX: {index}')
                # print(f'MORPHED HOURS[1]: {morphed_hours[1]}')
                # print(f"morphed_hours[1][index+1:index+3] {morphed_hours[1][index + 1:index + 3]}")
                # print(f"float(morphed_hours[1][index-2:index]): {float(morphed_hours[1][index-2:index])}")
                if morphed_hours[1][index+1:index+3] == '15':
                    # print('ping5')
                    # print(14)
                    temp_var = float(morphed_hours[1][index-2:index]) + 0.25
                elif morphed_hours[1][index+1:index+3] == '30':
                    # print(15)
                    temp_var = float(morphed_hours[1][index-2:index]) + 0.50
                    # print('ping6')
                elif morphed_hours[1][index+1:index+3] == '45':
                    # print(16)
                    temp_var = float(morphed_hours[1][index-2:index]) + 0.75
                    # print('ping7')
        utc_new_end = temp_var
        # utc_new_end = morphed_hours[1][14:16]
        # print(f'boing{utc_new_start}, {utc_new_end}')  #here is step 7
        # print(f'MORPHED HOURS[0]: {morphed_hours[0][:10]}, MORPHED_HOURS[1]: {morphed_hours[1][:10]}')
        if morphed_hours[0][:10] != morphed_hours[1][:10] and morphed_hours[0][:10] != incoming_date:    #dates are different, so..
            #add each hour in seperately.
            # print('yo')
            #---START HOURS---#
            try:
                # print(1)
                current_list = date_utc_corrected[morphed_hours[0][:10]] #drawing start hours
                current_list.append(utc_new_start)
                date_utc_corrected.update({morphed_hours[0][:10]: current_list})
                # print(f'TRY {date_utc_corrected[morphed_hours[0][:10]]}')
                # print('1a')
            except Exception as e: #IF start hour doesn't exist, make it and place the time inside.
                # print(f'E: {e}')
                date_utc_corrected[morphed_hours[0][:10]] = []
                date_utc_corrected[morphed_hours[0][:10]].append([utc_new_start])
                # print(f'EXCEPT {date_utc_corrected}')
                # print(2)
            #---END HOURS---#
            try:
                # print(3)
                current_list_2 = date_utc_corrected[morphed_hours[1][:10]]
                current_list_2.append(utc_new_end)
                date_utc_corrected.update({morphed_hours[1][:10]: current_list_2})
                # print(f'TRY 2 {date_utc_corrected[morphed_hours[1][:10]]}')
                # print('3a')
            except Exception as e: # start day doesn't exist, so make it and place time inside.
                # print(4)
                # print(f'E2: {e}')
                date_utc_corrected[morphed_hours[1][:10]] = []
                date_utc_corrected[morphed_hours[1][:10]].append([utc_new_end])
                # print(f'EXCEPT {date_utc_corrected}')
                # print(4)

        else: # dates match
            # print(f'DATES MATCHING')
            try:
                if new_date_1 == new_date_2: # If they have the same dates (a full lesson falls in the new day bracket)
                    date_utc_corrected[new_date_1].append([utc_new_start,utc_new_end])
                    # print(f'DATES MATCH: {date_utc_corrected}')
            except KeyError as e:  #if the value hasn't been created yet..
                # print(f'ERCEPTION E: {e}')
                date_utc_corrected[new_date_1] = []
                date_utc_corrected[new_date_1].append([utc_new_start,utc_new_end])
                # print(f'utc corrected {date_utc_corrected}')
    # print(f'Date utc corrected: {date_utc_corrected}')
        if final_conversion == 'round':  # Performs a rounding
            # print(f'PERFORMING ROUNDING WITH THESE VARS: {date_utc_corrected, date_utc_corrected, "full"}')
            date_utc_corrected = round_all_calendar_times(date_utc_corrected, date_utc_corrected, 'full')
    return date_utc_corrected  #Dictionary with new dates
        #if spread over multiple days, either create the day or add it to the proceeding day.

def convert_user_hours_to_utcstring(incoming_date, incoming_time_of_day):
    '''in a whole-hour or gradiated way.'''
    # print(f'CONVERT USER HOUR TO UTC_STRING {incoming_date}, {incoming_time_of_day}')
    if type(incoming_time_of_day) == int: # must be a full hour.
        modified_hour = f"{incoming_date} {incoming_time_of_day}:00:00.00000"
    else:
        find_point = str(incoming_time_of_day).find('.')
        if str(incoming_time_of_day)[-3:] == '.25':   #9:15, etc.
            modified_hour = f"{incoming_date} {str(incoming_time_of_day)[:find_point]}:15:00.00000"
        elif str(incoming_time_of_day)[-2:] == '.5': #9:30 etc.
            modified_hour = f"{incoming_date} {str(incoming_time_of_day)[:find_point]}:30:00.00000"
        elif str(incoming_time_of_day)[-3:] == '.75':   #9:45, etc.
            modified_hour = f"{incoming_date} {str(incoming_time_of_day)[:find_point]}:45:00.00000"
    # print(f'RETURNING MODIFIED HOUR: {modified_hour}')
    return modified_hour


def generate_initial_calendar(rounded_unavailabilities, teacher, day_availabilities):
    '''Generates the calendar events for FullCalendar to render on-screen.'''
    lang = int(lang_cookie_check())
    try:
        print('INCOMING TO GENERATING CALENDAR:')
        # print(f'current offset: {teacher_gmt_offset}')
        counter = 0
        for k,v in rounded_unavailabilities.items():
            print(f'K: {k} V: {v}')
            counter += 1
            if counter == 5:
                break
        print(f'timetable owner: {teacher},selected event: {selected_event} ')
        print(f'day availabilities: {day_availabilities}')
    except Exception as e:
        print(f'GENERATING CALENDAR EXCEPTION TRIGGERED: {e}')
    calendar_events = []
    def weird_calendar_fn(calendar_events, dictionary_to_add_to_calendar):
        '''Takes the variable Calendar Events, which the program uses as its main source for calendar variables, and fills it with events.'''

        if len(calendar_events) != 0: #if the amount of calendar events
            for event in calendar_events:
                if dictionary_to_add_to_calendar['id'] == event['id']:
                    abort_var = True
                else:
                    abort_var = False
            if abort_var is True:
                pass
            else:
                calendar_events.append(dictionary_to_add_to_calendar)
        else:
            print('3g')
            calendar_events.append(dictionary_to_add_to_calendar) #simple calendar add.
    def return_dictionary_to_add(available,start,end):
        '''returns a dictionary to add to the calendar.'''
        # print(f'SELECTED EVENT: {selected_event[:13]}, START: {start[:13]}')
        text_color = '000000'
        if available is True:
            border_color, border_color = '000000','3788d8'
            background_color, title, timetable_route = '40c058', language_dict['timetable']['available'][lang], timetable_route_address
        else:
            background_color,border_color, title = 'dcdfd9', 'dcdfd9', language_dict['timetable']['unavailable'][lang]
        try:
            if selected_event[:13] == start[:13]: #selected event
                background_color = '21ff10'
                border_color = '000000'
            else:
                pass
        except Exception as e:
            # print(f'EXCEPTION: {e}')
            pass
        new_id = f'{start[:-3]}_{teacher}'
        return {'id': new_id, 'title': title, 'start': start, 'end': end,'backgroundColor': f'#{background_color}',
                'textColor': f'#{text_color}','borderColor': f'#{border_color}',}

    def serve_active_hours():
        '''serves a dictionary with active hours and non-active hours.'''
        active_hours_dict = {}
        for i in range(1, 24):
            active_hours_dict[i] = False
        main_lesson_hours = []
        for availability in day_availabilities:
            main_lesson_hours.append(int(availability))
        if main_lesson_hours[0] < main_lesson_hours[1]:
            for i in range(main_lesson_hours[0], main_lesson_hours[1]): #deleted the +1
                active_hours_dict[i] = True
        else:
            numbers_to_fill_before_midnight = 24 - main_lesson_hours[0]
            numbers_to_fill_after_midnight = main_lesson_hours[1]
            num_b4_midnight = numbers_to_fill_before_midnight
            for i in range(main_lesson_hours[0], main_lesson_hours[0] + num_b4_midnight):  #should draw i.e. 11t 14t 15t [...] 22t 23t
                active_hours_dict[i] = True
            for i in range(0,numbers_to_fill_after_midnight):
                active_hours_dict[i] = True
        return active_hours_dict

    def hour_rounder(t):
        # Rounds to nearest hour by adding a timedelta hour if minute >= 30
        return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour)
                + timedelta(hours=t.minute // 30))

    active_hours = serve_active_hours()
    print(f'ACTIVE HOURS: {active_hours} ')
    import copy
    # rounded_copy = copy.deepcopy(rounded_unavailabilities)
    # rounded_copy_spinner = copy.deepcopy(rounded_unavailabilities)
    print('THIS IS A DICTIONARY: THEREFORE IT IS GENERATING INITIAL VARIABLES')
    for date, no_availability_lesson_blocks in rounded_unavailabilities.items(): #for each day.    ('2022-01-01':[[12,11],...])
        # print(f'NO AVAILABILITY BLOCK: {no_availability_lesson_blocks}')
        # print('1')
        # 6b. If there is an open day, create a full day of availabilities.
        if len(no_availability_lesson_blocks) == 0: #Day is 100% available (2022-01-01: [])
            # 6b(i). Creates a day of all availables if there are no lesson, and the GMT is at +11 #TODO Update.
            # print('2')
            # print(f'day avails: {day_availabilities[0]} ... {day_availabilities[1]}')
            def blas(i):
                start_date, end_date = f'{date}T{str(i).zfill(2)}:00:00', f'{date}T{str((i+1)).zfill(2)}:00:00' #creates an hour block
                dictionary_to_add_to_calendar = return_dictionary_to_add(True, start_date, end_date)
                # print(f'start date:{start_date}')
                # print(f'end date: {end_date}')
                # print(f'dictionary to add to calendar: {dictionary_to_add_to_calendar}')
                weird_calendar_fn(calendar_events, dictionary_to_add_to_calendar)

            if int(day_availabilities[1]) < int(day_availabilities[0]):
                for i in range(0, int(day_availabilities[0])):
                    if active_hours[i] is not False:
                        blas(i)
                        # print(i)
                for i in range(int(day_availabilities[1]), 24):
                    if active_hours[i] is not False:
                        blas(i)
                        # print(i)
            else:
                for i in range(int(day_availabilities[0]), int(day_availabilities[1])):  #Create an open schedule for the day.
                    if active_hours[i] is not False:
                        # print(f'1b{i}')
                        blas(i)
        # 6c. When there are unavailabilities in the timetable.
        else:
            for i, active_dict_bool in active_hours.items():
                switch_var = 0
                lesson_written = False
                if active_dict_bool is True:
                    # 6c(i)2a. Loops through each unavailable lesson in the day.
                    for lesson_block in no_availability_lesson_blocks:
                        # print('7')
                        if i == lesson_block[0] and switch_var == 0:
                            # print('8')
                            start_date, end_date = f'{date}T{str(i).zfill(2)}:00:00', f'{date}T{str((i + 1)).zfill(2)}:00:00'
                            # print('3a')
                            dictionary_to_add_to_calendar = return_dictionary_to_add(False,start_date,end_date)
                            # print(f'ANOMALY: {start_date} {end_date}')
                            switch_var += 1
                            lesson_written = True
                            weird_calendar_fn(calendar_events, dictionary_to_add_to_calendar)
                            try:
                                if i + 2 == lesson_block[1]: #add another hour block
                                    # print('9')
                                    start_date, end_date = f'{date}T{str(i+1).zfill(2)}:00:00', f'{date}T{str((i + 2)).zfill(2)}:00:00'
                                    dictionary_to_add_to_calendar = return_dictionary_to_add(False,start_date,end_date)
                                    weird_calendar_fn(calendar_events, dictionary_to_add_to_calendar)
                                    lesson_written = True
                            except Exception:
                                print(f'EXCEPTION RAISED HERE: {Exception}')
                    if lesson_written is False:
                        # print('10')
                        # print(f'3c')
                        # print(f'HERE: {date}T{str(i).zfill(2)}:00:00 {date}T{str((i + 1)).zfill(2)}:00:00')
                        start_date, end_date = f'{date}T{str(i).zfill(2)}:00:00', f'{date}T{str((i + 1)).zfill(2)}:00:00'
                        dictionary_to_add_to_calendar = return_dictionary_to_add(True,start_date,end_date)
                        weird_calendar_fn(calendar_events, dictionary_to_add_to_calendar)
    print(f' ALL SAID AND DONE, LENGTH OF CALENDAR EVENTS IS: {len(calendar_events)}')
    print(f'Generated Calendar Events[0] in end gencal {calendar_events[0].keys()} {calendar_events[0].values()}')
    print('NEW: Trying to remove unavailable slots in the day...')
    server_utc_time = dt.utcnow()
    server_utc_time_string = dt.strftime(server_utc_time,"%Y-%m-%d %H:%M:%S.%f")
    teacher_local_time = add_subtract_utc(server_utc_time_string, 'GMT', user_prefs['teachers'][teacher]['timezone'][0])
    get_start_time = f'{teacher_local_time[:10]} {int(day_availabilities[0]):02d}:00:00.000000'
    print(f'START TIME: {get_start_time}')
    get_local_time_plus_three = hour_rounder(dt.strptime(teacher_local_time, datetime_template) + timedelta(hours=3))
    to_trim_list = []
    initial_time = int(day_availabilities[0])
    initial_end_time = int(dt.strftime(get_local_time_plus_three, datetime_template)[11:13]) + 1
    print(f'INITIAL DAY AVAILABILITIES: {initial_time} | INITIAL END TIME: {initial_end_time}')
    if initial_end_time < initial_time:  # TODO Potential fix - 4-3-22
        for i in range(int(day_availabilities[0]), 25):
            to_trim_list.append(f'{i:02d}:00:00')
    else:
        for i in range(int(day_availabilities[0]), int(dt.strftime(get_local_time_plus_three, datetime_template)[11:13]) + 1):
            to_trim_list.append(f'{i:02d}:00:00')
    print(f'trimmed list: {to_trim_list}')
    event_no = 0
    list_indexes = []
    for event in calendar_events:
        if event['id'][:10] == teacher_local_time[:10] or dt.strptime(event['id'][:10], "%Y-%m-%d") < dt.strptime(teacher_local_time[:10], "%Y-%m-%d"):  # TODO 6-4 - Add in trim for day before...
            if event['start'][11:19] in to_trim_list:
                print(f'trimming! {event_no} {event["start"]}')
                list_indexes.append(event_no)
            elif dt.strptime(event['id'][:10], "%Y-%m-%d") < dt.strptime(teacher_local_time[:10], "%Y-%m-%d"):  #Doing the trimming #TODO check this doesnt break everything
                list_indexes.append(event_no)
        event_no += 1
    print(f'TEACHER LOCAL TIME: {teacher_local_time} {type(teacher_local_time)}')
    list_indexes.reverse()
    print(f'reverse list index: {list_indexes} ')
    for i in list_indexes:
        calendar_events.pop(i)
    return calendar_events

def generate_modified_calendar(calendar_events, old_timezone, new_timezone, selected_event):
    print('WE ARE GENERATING A MODIFIED CALENDAR FROM A SUPPLIED ORIGINAL!')
    import copy
    last_calendar_events_tocopy = copy.deepcopy(calendar_events)
    loop_counter = 0
    for event_dict in calendar_events:  # each event is a dictionary.
        # print(f'PRINTING EVENT_DICT: {event_dict}')
        # for k, v in event_dict.items():
        start_time = event_dict['start']  # in formats 2022-01-11T10:00:00
        end_time = event_dict['end']
        start_time_in_string = f'{start_time[0:10]} {start_time[11:]}.00000'
        end_time_in_string = f'{end_time[0:10]} {end_time[11:]}.00000'
        start_time_in_string_adjusted = add_subtract_utc(start_time_in_string, old_timezone, new_timezone)
        start_time_in_string_reformatted = f'{start_time_in_string_adjusted[:10]}T{start_time_in_string_adjusted[11:16]}'
        end_time_in_string_adjusted = add_subtract_utc(end_time_in_string, old_timezone, new_timezone)
        end_time_in_string_reformatted = f'{end_time_in_string_adjusted[:10]}T{end_time_in_string_adjusted[11:16]}'
        last_calendar_events_tocopy[loop_counter]['start'] = start_time_in_string_reformatted
        last_calendar_events_tocopy[loop_counter]['end'] = end_time_in_string_reformatted
        # print(f'Old start: {start_time} New start: {last_calendar_events_tocopy[loop_counter]["start"]}')
        loop_counter += 1
    print(f"before: last_calendar_events[0]: {calendar_events[-1]}, after {last_calendar_events_tocopy[-1]}")
    return last_calendar_events_tocopy
# last_calendar_events = {}
