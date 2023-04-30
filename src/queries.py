from .dbcontainers import Auth_Login_Container, Auth_User_Container, Face_Identity_Container,\
                          Face_Vector_Container,Person_Alerts_container, Person_Attendance_Log_container, Person_Department_Container,\
                          Person_Holiday_Container, Person_Location_Container, Person_Person_Details_Container,\
                          Person_Roster_Container, Warehouse_Olddeptchange_Container, Warehouse_Oldempdept_Container,\
                          Warehouse_Oldempshifts_Container, DB_Container, Person_Category_Container, base_dataclass
from .dbutils import run_fetch_query,run_query_noreturn, create_connection
from typing import Tuple, List, Union, Any, Optional, Type,NoReturn
from sqlite3 import Connection
from datetime import datetime as datetimemodule, date as datemodule
from datetime import timedelta
from .global_vars import DATE_FORMAT
from pandas import to_datetime, DataFrame
from .utils import to_timestamp
from numpy import unique
from .load_config import CONFIG
import os

ALERT_CATEGORIES = CONFIG['ALERTS']['alert_categories'].split(",")
ALERT_CATEGORIES = [i for i in ALERT_CATEGORIES if i!=""]

def get_point_clause(column: List[str], value: List[str]) -> Tuple[List[str], Tuple[Optional[str], ...]]:

    conditions = []
    values = []

    for a, b in zip(column, value):
        if b:
            conditions.append(f'{a} = ?')
            values.append(b)
    
    clause = ' AND '.join(conditions)
    values = tuple(values)
    return clause, values

def get_similar_clause(column: List[str], value: List[str]) -> Tuple[List[str], Tuple[Optional[str], ...]]:

    conditions = []
    values = []

    for a, b in zip(column, value):
        if b:
            conditions.append(f'{a} = ?')
            values.append(b)
    
    clause = ' LIKE '.join(conditions)
    values = tuple(values)
    return clause, values

def get_misc_clause(column: List[str], value: List[str], delimeter: Optional[str] = ",") -> Tuple[List[str], Tuple[Optional[str], ...]]:

    conditions = []
    values = []

    for a, b in zip(column, value):
        if b!=None:
            conditions.append(f'{a} = ?')
            values.append(b)
    
    clause = delimeter.join(conditions)
    values = tuple(values)
    return clause, values

def get_range_clause(column: List[str], value: List[Tuple[Optional[str], Optional[str]]])-> Tuple[List[str], Tuple[Optional[str], ...]]:

    conditions = []
    values = []

    for a, b in zip(column, value):
        
        if b[0] is not None:
            conditions.append(f'{a} >= ?')
            values.append(b[0])
        
        if b[1] is not None:
            conditions.append(f'{a} <= ?')
            values.append(b[1])
        
    clause = ' AND '.join(conditions)
    values = tuple(values)

    return clause, values

def run_select_query(conn: Connection, query: str, values: Tuple[Any, ...], container: Optional[Type[DB_Container]]=None, return_dc: bool=False) -> List[Union[str, base_dataclass]]:

    result = run_fetch_query(conn, query, values=values)
    # print(query,values)
    # print(result)
    if return_dc:
        result = [container.make(res) for res in result]
    
    return result

        

def format_query(query: str, clause: str) -> str:

    if len(clause) > 0:
        query = f'{query} WHERE {clause}'
    
    return query

# Basic Select Queries

def select_from_auth_login(conn: Connection , username: Optional[str] = None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Auth_Login_Container.field.tablename}'
    clause, values = get_point_clause(['username'], [username])
    query = format_query(query, clause)
    
    return run_select_query(conn, query, values, Auth_Login_Container, return_dc=return_dc)

def select_from_auth_user(conn: Connection, username: Optional[str]=None, role: Optional[str]=None, name: Optional[str] =None, return_dc: bool=False, point_clause: bool = True) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM {Auth_User_Container.field.tablename}'
    clause, values = None, None
    if point_clause:
        clause, values = get_point_clause(['username', 'role', 'name'], [username, role, name])
    else:
        clause, values = get_similar_clause(['username', 'role', 'name'], [username, role])
    
    
    query = format_query(query, clause)

    return run_select_query(conn, query, values, Auth_User_Container, return_dc=return_dc)

def select_from_face_vectors(conn: Connection, empid: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Face_Vector_Container.field.tablename}'
    clause, values = get_point_clause(['empid'], [empid])
    query = format_query(query, clause)

    return run_select_query(conn, query, values, Face_Vector_Container, return_dc=return_dc)

def select_from_face_identity(conn: Connection, empid: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Face_Identity_Container.field.tablename}'
    clause, values = get_point_clause(['empid'], [empid])
    query = format_query(query, clause)
    
    # print(query, values)
    return run_select_query(conn, query, values, Face_Identity_Container, return_dc=return_dc)

def select_from_attendance_logs(conn: Connection, empid: Optional[str]=None, start_date: Optional[str]=None,
                                end_date: Optional[str]=None, firstlocation: Optional[str]=None, 
                                lastseenlocation: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM {Person_Attendance_Log_container.field.tablename}'
    point_clause, point_values = get_point_clause(['empid', 'firstlocation', 'lastseenlocation'], 
                                                  [empid, firstlocation, lastseenlocation])
    range_clause, range_values = get_range_clause(['date'], 
                                                  [(start_date, end_date)])
    if range_clause:
        clause = point_clause + ' AND ' + range_clause
        values = list(point_values) + list(range_values)
    query = format_query(query, clause)
    
    # print(query, values)

    return run_select_query(conn, query, values, Person_Attendance_Log_container, return_dc=return_dc)

def select_from_hrms_attendance_logs(conn: Connection, empid: Optional[str]=None, Punch_Date_Time: Optional[str]=None,
                                Record_LastUpdated: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM attendance_logs'
    point_clause, point_values = get_point_clause(['emp_id'],
                                                  [empid])
    range_clause, range_values = get_range_clause(['Punch_Date_Time'],
                                                  [(str(Punch_Date_Time), str(Record_LastUpdated+ timedelta(days=1)))])
    if range_clause:
        clause = point_clause + ' AND ' + range_clause
        values = list(point_values) + list(range_values)
    query = format_query(query, clause)

    # print('hrms',query, values)

    return run_select_query(conn, query, values, return_dc=return_dc)

def select_from_category(conn: Connection, name: Optional[str] = None, cattype: Optional[str] = None, return_dc: bool = False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    query = f'SELECT * FROM {Person_Category_Container.field.tablename}'
    clause, values = get_point_clause(['name','cattype'], [name, cattype])
    query = format_query(query, clause)

    return run_select_query(conn, query, values, Person_Category_Container, return_dc=return_dc)
    

def select_from_department(conn: Connection, deptid: Optional[str] = None, deptname: Optional[str] = None, location: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM {Person_Department_Container.field.tablename}'
    clause, values = get_point_clause(['deptid','deptname','location'], [deptid, deptname, location])
    query = format_query(query, clause)

    return run_select_query(conn, query, values, Person_Department_Container, return_dc=return_dc)

def select_from_holiday(conn: Connection, date: Optional[str]=None,fromdate: Optional[str]=None, todate: Optional[str]=None,htype: Optional[str]=None, name: Optional[str]=None, deptid: Optional[str]=None, year: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM {Person_Holiday_Container.field.tablename}'
    clause, values = get_point_clause(['date','deptid','htype', 'name'], [date, deptid, htype, name])
    
    if year:
        fromdate =str(datemodule(day=1, month= 1, year= year))
        todate =str(datemodule(day=31, month= 12, year= year))
    
    range_clause, range_values = get_range_clause(['date'], 
                                                  [(fromdate, todate)])
    
    
    if range_clause:
        if clause:
            clause = clause + ' AND ' + range_clause
            values = tuple(list(values) + list(range_values))
        else:
            clause = range_clause
            values = range_values
    query = format_query(query, clause)
    
    # print(query, values)
    return run_select_query(conn, query, values, Person_Holiday_Container, return_dc=return_dc)

def select_from_locations(conn: Connection, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:

    query = f'SELECT * FROM {Person_Location_Container.field.tablename}'
    return run_select_query(conn, query, (), Person_Location_Container, return_dc=return_dc)

def select_from_person_details(conn: Connection, empid: Optional[str]=None, name: Optional[str] = None, empstatus: Optional[str]=None, 
                                currdept: Optional[str]=None, currshift: Optional[str]=None, 
                                location: Optional[str]=None, return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Person_Person_Details_Container.field.tablename}'

    clause, values = get_point_clause(['empid', 'empstatus', 'name','currdept', 'currshift', 'location'],
                                      [empid, empstatus, name, currdept, currshift, location])
    
    query = format_query(query, clause)
    return run_select_query(conn, query, values, Person_Person_Details_Container, return_dc=return_dc)

def select_from_person_roster(conn: Connection, rid: Optional[str]=None, name: Optional[str] = None, offday: Optional[str]=None,
                        return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Person_Roster_Container.field.tablename}'
    clause, values = get_point_clause(['rid', 'name', 'offday'], [rid, name, offday])
    query = format_query(query, clause)

    return run_select_query(conn, query, values, Person_Roster_Container, return_dc=return_dc)

def select_from_person_alerts(conn: Connection, alertid: Optional[int]=None, empid: Optional[str]=None, datetime: Optional[str]=None,start_date: Optional[str]=None,end_date: Optional[str]=None, location: Optional[str]=None, extra_clause: Optional[str]=None ,return_dc: bool=False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Person_Alerts_container.field.tablename}'

    clause, values = get_point_clause(['alertid', 'empid', 'datetime', 'location'],
                                      [alertid, empid, datetime, location])
    
    range_clause, range_values = get_range_clause(['date'], 
                                                  [(start_date, end_date)])
    
    
    # clause = clause + range_clause
    # values = list(values) + list(range_values)
    
        
    if range_clause:
        if clause:
            clause = clause + ' AND ' + range_clause
            values = tuple(list(values) + list(range_values))
        else:
            clause = range_clause
            values = range_values
            
    if extra_clause!=None:
        clause=clause+" "+extra_clause       
        
    query = format_query(query, clause)
    
    # print(query, values)
    return run_select_query(conn, query, values, Person_Alerts_container, return_dc=return_dc)

def select_from_person_department(conn: Connection, deptid : Optional[str] = None, deptname: Optional[str] = None, location: Optional[str] = None, depthod: Optional[str] = None, return_dc : bool = False) -> List[Union[Tuple[Any, ...], base_dataclass]]:
    
    query = f'SELECT * FROM {Person_Department_Container.field.tablename}'
    
    clause, values = get_point_clause(['deptid', 'deptname', 'location', 'depthod'],[deptid, deptname, location, depthod])
    
    query = format_query(query, clause)
    
    return run_select_query(conn, query, values, Person_Department_Container, return_dc = return_dc)

# Join Select Queries

#queries old
def get_person_log(conn: Connection, identity: str, _date: str, _location: Optional[str]=None,return_dc: bool=False,online: bool=True)->List[Union[Tuple[Any, ...], base_dataclass]]:
    return select_from_attendance_logs(conn, empid = identity,start_date = _date, end_date = _date, firstlocation = _location, lastseenlocation = _location, return_dc = return_dc)

def get_hrms_person_log(conn: Connection, identity: str, _date: str, _location: Optional[str]=None,return_dc: bool=False,online: bool=True)->List[Union[Tuple[Any, ...], base_dataclass]]:
    return select_from_hrms_attendance_logs(conn, empid = identity,Punch_Date_Time = _date, Record_LastUpdated = _date, return_dc = return_dc)

def create_person_log(conn: Connection, identity: str, _date: str, in_time: str, out_time: Optional[str]=None, firstlocation: Optional[str]=None, lastseenlocation: Optional[str]=None,online: bool=True) -> NoReturn :
    if out_time is None:
        out_time = in_time
    
    if firstlocation is None:
        firstlocation = ''
        
    if lastseenlocation is None:
        lastseenlocation = firstlocation 
        
    columns = [
        Person_Attendance_Log_container.field.empid,
        Person_Attendance_Log_container.field.intime,
        Person_Attendance_Log_container.field.outtime,
        Person_Attendance_Log_container.field.date,
        Person_Attendance_Log_container.field.firstlocation,
        Person_Attendance_Log_container.field.lastseenlocation
    ]
    
    column_order = ', '.join(columns)
    values_q = ', '.join(['?'] * len(columns))
    
    query = f'INSERT INTO {Person_Attendance_Log_container.field.tablename}({column_order}) VALUES({values_q})'
    values = (identity, in_time, out_time, _date, firstlocation, lastseenlocation)

    # print(query)
    run_query_noreturn(conn, query, values)

def create_hrms_person_log(conn: Connection, identity: str, _date: str, in_time: str, out_time: Optional[str]=None, firstlocation: Optional[str]=None, lastseenlocation: Optional[str]=None,online: bool=True) -> NoReturn :
    if out_time is None:
        out_time = datetimemodule.now()

    # Check for push flag if yes then push
    dept_details = select_from_person_department(conn)
    person_details = select_from_person_details(conn, identity)
    dept_flag_list = [dept_details[i][0] for i in range(len(dept_details)) if dept_details[i][-1]=='y']

    # print(dept_flag_list,in_time, out_time)
    if person_details[0][3] in dept_flag_list:
        # print('person_details', person_details)
        con = create_connection(CONFIG['DB']['db_for_hrms'])
        # values_q_hr = (identity, in_time)
        query_hrms_db = f'INSERT INTO attendance_logs(emp_id, Punch_Date_Time, Record_LastUpdated) VALUES(?, ?, ?)'
        values_hrms_db = (identity, in_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], out_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        run_query_noreturn(con, query_hrms_db, values_hrms_db)

    # print('x query hrms', query_hrms_db)
    
def update_person_log(conn:Connection, fetched_result:base_dataclass, identity:str, _date:str, _time:str, _location:str,online: bool=True) -> NoReturn :

    # last_seen_time = to_datetime(fetched_result.outtime)
    # if (_time - last_seen_time).seconds < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
    #     return
    # else:
        # query = f'UPDATE {Person_Attendance_Log_container.field.tablename} SET {Person_Attendance_Log_container.field.outtime} = ?, {Person_Attendance_Log_container.field.lastseenlocation} = ? WHERE {Person_Attendance_Log_container.field.empid} = ? AND {Person_Attendance_Log_container.field.date} = ?'
        # values = (_time, _location, identity, _date)
    query = f'UPDATE {Person_Attendance_Log_container.field.tablename} SET {Person_Attendance_Log_container.field.intime} = ?,{Person_Attendance_Log_container.field.outtime} = ?, {Person_Attendance_Log_container.field.firstlocation} = ?, {Person_Attendance_Log_container.field.lastseenlocation} = ? WHERE {Person_Attendance_Log_container.field.empid} = ? AND {Person_Attendance_Log_container.field.date} = ? AND {Person_Attendance_Log_container.field.intime} = ? AND {Person_Attendance_Log_container.field.firstlocation} = ?'
    values = (_time, _time, _location, _location, identity, _date, fetched_result.outtime, fetched_result.lastseenlocation)

    run_query_noreturn(conn, query, values)

def update_hrms_person_log(conn:Connection, fetched_result:list, identity:str, _date:str, _time:str, _location:str,online: bool=True) -> NoReturn :
    # Check for push flag if yes then push
    dept_details = select_from_person_department(conn)
    person_details = select_from_person_details(conn, identity)
    dept_flag_list = [dept_details[i][0] for i in range(len(dept_details)) if dept_details[i][-1]=='y']

    out_time = datetimemodule.now()

    # print(dept_flag_list,in_time, out_time.strftime("%Y-%m-%d %H:%M:%S"))
    if person_details[0][3] in dept_flag_list:
        # print('person_details', person_details)
        con = create_connection(CONFIG['DB']['db_for_hrms'])
        # values_q_hr = (identity, in_time)
        query_hrms_db = f'UPDATE attendance_logs SET Punch_Date_Time = ?, Record_LastUpdated = ? WHERE emp_id = ? AND Punch_Date_Time = ? AND Record_LastUpdated = ? '
        values_hrms_db = (_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], out_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], identity, fetched_result[2], fetched_result[4])
        run_query_noreturn(con, query_hrms_db, values_hrms_db)

    # print('x query hrms', query_hrms_db)

def add_person_log(conn:Connection, fetched_result:base_dataclass, identity:str, _date:str, _time:str, _location:str,online: bool=True) -> NoReturn :

    last_seen_time = to_datetime(fetched_result.outtime)
    if (_time - last_seen_time).seconds < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
        return
    else:
        # print("cre",_time)
        create_person_log(conn, identity, _date, _time, out_time=_time, firstlocation=_location, lastseenlocation=_location, online=online)
        
        
def get_threat_status(conn:Connection, identity:str) -> Optional[str]:

    res = select_from_person_details(conn,empid=identity,return_dc=True)
    if len(res)==0:
        return None
    else:
        return res[0].empstatus
    
def get_previous_alert(conn:Connection, identity:str, _date:str) -> Tuple[Optional[Union[str,int,datetimemodule]]]:
    extra_clause=f'ORDER BY {Person_Alerts_container.field.datetime} DESC'
    res= select_from_person_alerts(conn, empid=identity, start_date =_date, end_date = _date, extra_clause=extra_clause,return_dc=True)
    if len(res)==0:
        return None,None,None
    else:
        res_dc=res[0]
        return res_dc.alertid,res_dc.datetime,res_dc.location
    
def update_alert(conn:Connection, _time:str, alertid: int) -> NoReturn:
    query = f'UPDATE {Person_Alerts_container.field.tablename} SET {Person_Alerts_container.field.datetime} = ? WHERE {Person_Alerts_container.field.alertid} = ?'
    run_query_noreturn(conn, query, (_time, alertid))
    
def insert_alert(conn:Connection, identity:str, _time: str, _date: str, _location: str) -> NoReturn :
    
    query = f'INSERT INTO {Person_Alerts_container.field.tablename}({Person_Alerts_container.field.empid}, {Person_Alerts_container.field.datetime}, {Person_Alerts_container.field.date}, {Person_Alerts_container.field.location}) VALUES(?, ?, ?, ?)'
    run_query_noreturn(conn, query, (identity, _time, _date, _location))
    
def create_alert(conn: Connection, identity: str, _date: str, _time: str, _location: str) -> NoReturn :
    
    row_id, prev_alert_time, prev_location = get_previous_alert(conn, identity, _date)
    run_insert_alert = True

    if prev_alert_time:
        if prev_location == _location:
            if (_time - prev_alert_time).seconds > int(CONFIG['ALERTS']['alert_interval']):
                update_alert(conn, _time, row_id)
            run_insert_alert = False
    
    if run_insert_alert:
        insert_alert(conn, identity, _time, _date, _location)
        
def check_faces(conn: Connection, identity: str, _date: str, _time: str, _location: str, online: bool = True) -> Union[str,NoReturn]:
    
#     rows = get_person_log(conn, identity=identity, _date=_date, _location=_location, online=online, return_dc= True)
#     # print("cf",len(rows))
#     if not rows:
#         create_person_log(conn, identity, _date=_date, in_time=_time, firstlocation =_location, online=online)
#     else:
# #         print("rows last: ",rows)
#         #update_person_log(conn, rows[0], identity, _date, _time, _location, online=online)
#         add_person_log(conn, rows[-1], identity, _date, _time, _location, online=online)

    # rows = get_person_log(conn, identity=identity, _date=_date, _location=_location, online=online, return_dc= True)
    rows_all = get_person_log(conn, identity=identity, _date=_date, _location=None, online=online, return_dc= True)
    if not os.path.exists(CONFIG['DB']['db_for_hrms']):
        print("DB hrms path NOT EXISTS",CONFIG['DB']['db_for_hrms'])
        conn_hrms = create_connection(CONFIG['DB']['db_for_hrms'])
        query_hrms = "CREATE TABLE attendance_logs (id INTEGER PRIMARY KEY NOT NULL, emp_id VARCHAR NOT NULL, Punch_Date_Time DATETIME, is_Read INTEGER DEFAULT (0), Record_LastUpdated DATETIME);"
        res_hrms = run_query_noreturn(conn_hrms, query_hrms)
        if res_hrms:
            print("NEW EMPTY HRMS DB CREATED")
        else:
            print("NEW HRMS DB CREATION FAILED")
            try:
                conn_hrms.rollback()
                os.remove(CONFIG['DB']['db_for_hrms'])
            except:
                pass
        conn_hrms.close()
    # else:
    #     print("DB hrms path EXITS ",CONFIG['DB']['db_for_hrms'])    



    con = create_connection(CONFIG['DB']['db_for_hrms'])


    ###HRMS CODE
    rows_all_hrms = get_hrms_person_log(con, identity=identity, _date=_date, _location=None, online=online, return_dc= False)
    # print("cf",len(rows_all_hrms), len(rows_all), _date)

    if not rows_all_hrms:
        create_hrms_person_log(conn, identity, _date=_date, in_time=_time, online=online)
    else:
        last_row = rows_all_hrms[-1]
        # print('last row',last_row)
        last_seen_time = to_datetime(last_row[2])
        gap_time = (_time - last_seen_time).seconds
        if gap_time < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
            if len(rows_all_hrms)<2:
                if len(rows_all_hrms)==1:
                    update_hrms_person_log(conn, rows_all_hrms[-1], identity, _date, _time, _location, online=online)
                else:
                    pass
            else: pass
        else:
            create_hrms_person_log(conn, identity, _date=_date, in_time=_time, firstlocation =_location, online=online)
            

    if not rows_all:
        # print(1)
        create_person_log(conn, identity, _date=_date, in_time=_time, firstlocation =_location, online=online)
    else:
        last_row = rows_all[-1]
        lastseenlocation = last_row.lastseenlocation
        last_seen_time = to_datetime(last_row.outtime)
        gap_time = (_time - last_seen_time).seconds
        if _location == lastseenlocation:
    #         print("rows last: ",rows)
            #update_person_log(conn, rows[0], identity, _date, _time, _location, online=online)
            # print(2)
            add_person_log(conn, rows_all[-1], identity, _date, _time, _location, online=online)
        else:
            if gap_time < int(CONFIG['RECOGNITION']['update_last_seen_sec']):
                if len(rows_all)<2:
                    # print(3)
                    #TODO check for when first log is exit
                    if len(rows_all)==1 and lastseenlocation == "EXIT":
                        update_person_log(conn, rows_all[-1], identity, _date, _time, _location, online=online)
                    pass
                else:
                    prev_location = rows_all[-2].lastseenlocation
                    if prev_location != _location:
                        # print(4)
                        update_person_log(conn, rows_all[-1], identity, _date, _time, _location, online=online)
                    else:
                        # print(5)
                        pass
                        # add_person_log(conn, rows[-1], identity, _date, _time, _location, online=online)
            else:
                # print(6)
                add_person_log(conn, rows_all[-1], identity, _date, _time, _location, online=online)


    # Check alert and then update
    if online:
        threat_status=get_threat_status(conn, identity)
        if threat_status==None:
            return 'welcome'
        if threat_status in ALERT_CATEGORIES:
            create_alert(conn, identity=identity, _date=_date, _time=_time, _location=_location)
            return 'guard'
        else:
            return 'welcome'

        
# def update_fractions(conn: Connection, identity: str, value: str ):
    
#     query = f'UPDATE {OFFLINE_LOG_TABLE_FIELDS.table_name} SET {OFFLINE_LOG_TABLE_FIELDS.field_duration_seen} = ? WHERE {OFFLINE_LOG_TABLE_FIELDS.field_identity} = ?'
#     values = (value, identity)
#     run_query_noreturn(conn, query, values)


def check_username_for_login(conn: Connection, username: str) -> bool :
    
    if not username:
        return False
    
    res=select_from_auth_user(conn,username=username)
    
    # print(res)
    if res!=None:
        return len(res) > 0
    else:
        return False
    
def retrieve_user_info(conn: Connection, username:str)-> Tuple[Optional[str]]:
    
    if not username:
        return None, None
    
    res=select_from_auth_user(conn,username=username,return_dc=True)
    
    if len(res)==0:
        return None,None
    else:
        res_dc=res[0]
        return res_dc.password,res_dc.role
    
    
def search_all(face_db_connection: Connection, person_db_connection: Connection, return_dc: bool = False) -> Tuple[List[Union[str,base_dataclass]]]:
    
    person_details = select_from_person_details(person_db_connection,return_dc= return_dc)
    fd = {}

    if person_details is not None:
        for row in person_details:
            empid = None
            if return_dc:
                empid=row.empid
            else:
                empid = row[Person_Person_Details_Container.enum.empid.value]
            res = select_from_face_vectors(face_db_connection,empid=empid,return_dc=True)
            if len(res)> 0:
                fd[empid] = [res[0].label]
            else:
                fd[empid]=res
                
    return person_details, fd


def search_by(face_db_connection: Connection, person_db_connection: Connection, colname:str, value: str, exact:bool, return_dc : bool = False) -> Tuple[List[Union[str,base_dataclass,Tuple[Any, ...]]]]:
    if exact:
        query = f'SELECT * FROM {Person_Person_Details_Container.field.tablename} WHERE {colname} = ?'
        search_tuple = (value, )
    else:
        query = f'SELECT * FROM {Person_Person_Details_Container.field.tablename} WHERE {colname} LIKE ?'
        search_tuple = (f'%{value}%', )

    person_details = run_select_query(person_db_connection, query=query, values=search_tuple,container=Person_Person_Details_Container,return_dc= return_dc)
    fd = {}

    if person_details is not None:
        for row in person_details:
            empid = None
            if return_dc:
                empid=row.empid
            else:
                empid = row[Person_Person_Details_Container.enum.empid.value]
            res = select_from_face_vectors(face_db_connection,empid=empid,return_dc=True)
            if len(res)> 0:
                fd[empid] = [res[0].label]
            else:
                fd[empid] = res
                
    return person_details, fd

def search_by_id(face_db_connection: Connection, person_db_connection: Connection, value: str, exact:bool, return_dc : bool = False) -> Tuple[List[Union[str,base_dataclass]]]:
    return search_by(face_db_connection, person_db_connection, Person_Person_Details_Container.field.empid, value, exact, return_dc = return_dc)

def search_by_name(face_db_connection: Connection, person_db_connection: Connection, value: str, exact:bool, return_dc : bool = False) -> Tuple[List[Union[str,base_dataclass]]]:
    return search_by(face_db_connection, person_db_connection, Person_Person_Details_Container.field.name, value, exact, return_dc = return_dc)

def update_person_status(person_db_connection: Connection, _id: str, status: str) -> NoReturn:

    query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.empstatus}=? WHERE {Person_Person_Details_Container.field.empid} = ?'
    run_query_noreturn(person_db_connection, query, (status, _id))

def update_person_name(person_db_connection: Connection, _id: str, name: str) -> bool:

    query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.name}=? WHERE {Person_Person_Details_Container.field.empid} = ?'
    return run_query_noreturn(person_db_connection, query, (name, _id))
    
def archive_employee_shift(warehouse_db_connection: Connection, empid: str, datetime: str, shiftid:str, starttime: str, endtime: str, offday: str, fromdate: str, todate: str, shiftname: str) -> bool :
    query= f'INSERT INTO {Warehouse_Oldempshifts_Container.field.tablename}({Warehouse_Oldempshifts_Container.field.empid},{Warehouse_Oldempshifts_Container.field.datetime}, {Warehouse_Oldempshifts_Container.field.shift}, {Warehouse_Oldempshifts_Container.field.starttime},{Warehouse_Oldempshifts_Container.field.endtime}, {Warehouse_Oldempshifts_Container.field.offday},{Warehouse_Oldempshifts_Container.field.fromdate},{Warehouse_Oldempshifts_Container.field.todate},{Warehouse_Oldempshifts_Container.field.shiftname}) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'
    
    values=(empid,datetime,shiftid,starttime,endtime,offday,fromdate,todate,shiftname)
    
    return run_query_noreturn(warehouse_db_connection,query,values)
    

def update_employee_shift_details(person_db_connection: Connection, _empid: str, shiftid: str) -> bool:
                  
    query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.currshift}=?,{Person_Person_Details_Container.field.shifttimestamp}=? WHERE {Person_Person_Details_Container.field.empid} = ?'
    
    curr_timestamp= datetimemodule.now()
    r1 = run_query_noreturn(person_db_connection, query, (shiftid,str(curr_timestamp), _empid))
          
    if not r1:
        return False
    

    
    return True
    

def update_employee_department_details(person_db_connection: Connection, _empid: str, deptid: str) -> bool:

    person_details=select_from_person_details(person_db_connection,empid= _empid, return_dc=True)[0]
    olddept_id, olddept_timestamp = person_details.currdept, person_details.depttimestamp
    
    if olddept_id == deptid:
        return True
    
    newdept_details = select_from_person_department(person_db_connection, deptid = deptid, return_dc=True)[0]
    
    location = newdept_details.location

    query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.currdept}=?,{Person_Person_Details_Container.field.depttimestamp}=? ,{Person_Person_Details_Container.field.location}=? WHERE {Person_Person_Details_Container.field.empid} = ? '
    
    curr_timestamp= datetimemodule.now()
    r1 = run_query_noreturn(person_db_connection, query, (deptid, str(curr_timestamp), location, _empid))
          
    if not r1:
        return False
    
    return True
    
def update_department_details(person_db_connection: Connection,  deptid: str, deptname : Optional[str] = None, location: Optional[str] = None, depthod: Optional[str] = None, check_for_update: Optional[bool]= False) -> Union[bool,int]:
    
    # print("na",deptid, deptname, location, depthod)
    if check_for_update:
        if location!=None or deptname!=None:
            dept_details_db = select_from_person_department(person_db_connection, deptname = deptname, location = location, return_dc=True)
            # print("db",dept_details_db)
            if len(dept_details_db)>0:
                # print(3)
                return -1
    
    if location!=None and deptname!=None:
        dept_details_db = select_from_person_department(person_db_connection, deptname = deptname, location = location, return_dc=True)
        # print("db",dept_details_db)
        if len(dept_details_db)>0:
            # print(3)
            return False
    
    
    set_clause_columns = []
    set_clause_values = []
    
    if deptname != None:
        set_clause_columns.append(Person_Department_Container.field.deptname)
        set_clause_values.append(deptname)
        
    if location != None:
        set_clause_columns.append(Person_Department_Container.field.location)
        set_clause_values.append(location)
        
    if depthod != None:
        set_clause_columns.append(Person_Department_Container.field.depthod)
        set_clause_values.append(depthod)
    
    if not len(set_clause_values) > 0:
        return False
    
    curr_timestamp= datetimemodule.now()
    set_clause_columns.append(Person_Department_Container.field.timestamp)
    set_clause_values.append(str(curr_timestamp))
    set_clause, _ = get_misc_clause(set_clause_columns, set_clause_values)
    dept_update_query = f'UPDATE {Person_Department_Container.field.tablename} SET '+ set_clause + f' WHERE {Person_Department_Container.field.deptid} = ?'
    
    set_clause_values.append(deptid)
    dept_update_values = tuple(set_clause_values)
    r1 = run_query_noreturn(person_db_connection, dept_update_query, dept_update_values)
    
    if not r1:
        # print(1)
        return False
                
    
#     query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.depttimestamp} = ?' 
#     if location:
#         query += f', {Person_Person_Details_Container.field.location} = ?'
#     where_clause = f' WHERE {Person_Person_Details_Container.field.currdept} = ?'
#     query += where_clause
    
#     values = None
#     if location:
#         values = (str(curr_timestamp), location, deptid)
#     else:
#         values = (str(curr_timestamp), deptid)
#     r3 = run_query_noreturn(person_db_connection, query, values)
     
#     if not r3:
#         return False
    if location:
        query = f'UPDATE {Person_Person_Details_Container.field.tablename} SET {Person_Person_Details_Container.field.location} = ?  WHERE {Person_Person_Details_Container.field.currdept} = ?'
        values = (location, deptid)
        r3 = run_query_noreturn(person_db_connection, query, values)
        
        if not r3:
            return False
        
    return True
        
    
def fetch_alerts(person_db_connection: Connection, start_date: str, end_date: str, empid: Optional[str] = None) -> Tuple[DataFrame, List[str]] :

    res = select_from_person_alerts(person_db_connection, start_date = start_date, end_date = end_date, empid = empid) 

    res_df = DataFrame([])
    unique_emp_ids = []
    if res:
        res_df = DataFrame(res, columns=['alertid', 'empid', 'datetime', 'date', 'location'])
        unique_emp_ids = list(res_df['empid'].unique())
    
    return res_df, unique_emp_ids

def get_cameras_from_db(person_db_connection: Connection)-> List[str]:

    result = []
    for colname in [Person_Attendance_Log_container.field.firstlocation, Person_Attendance_Log_container.field.lastseenlocation]:
        query = f'SELECT DISTINCT {colname} FROM {Person_Attendance_Log_container.field.tablename}'
        res = run_fetch_query(person_db_connection, query)
        for v in res:
            result.append(v[0])
            
    return unique(result).tolist()

def get_roster_from_db(person_db_connection: Connection, return_dc : bool = False) ->  List[Union[Tuple[Any, ...], base_dataclass]]:
    
    return select_from_person_roster(person_db_connection,return_dc= return_dc)

def get_department_from_db(person_db_connection: Connection, deptid: Optional[str] = None, return_dc : bool = False) ->  List[Union[Tuple[Any, ...], base_dataclass]]:

    return select_from_person_department(person_db_connection, deptid = deptid, return_dc= return_dc)

def get_shift_timing_from_db(person_db_connection: Connection, shiftid: str, return_dc : bool = False)->  List[Union[Tuple[Any, ...], base_dataclass]]:

    return select_from_person_roster(person_db_connection, rid= shiftid, return_dc = return_dc)

def get_category_from_db(person_db_connection: Connection, name: Optional[str] = None, cattype: Optional[str] = None, return_dc: bool = False) ->  List[Union[Tuple[Any, ...], base_dataclass]]:
    
    return select_from_category(person_db_connection, name = name, cattype = cattype, return_dc = return_dc)

def get_hod_list_from_db(person_db_connection: Connection, deptid : Optional[str] = None) ->  List[str]:
    res = select_from_person_department(person_db_connection, return_dc = True)
    hod_names = []
    for dc in res:
        hod_names.append(dc.depthod)
    return list(set(hod_names))

def insert_operator_info(auth_db_connection: Connection, operator_id: str, operator_pass: str, operator_name: str, operator_role: str) -> bool:
    
    fetch_query = f'SELECT {Auth_User_Container.field.username} FROM {Auth_User_Container.field.tablename} where {Auth_User_Container.field.username} = ?'
    res = run_fetch_query(auth_db_connection, fetch_query, (operator_id,), fetch_type='one')
    
    if res is None:
        query = f'INSERT INTO {Auth_User_Container.field.tablename}({Auth_User_Container.field.username}, {Auth_User_Container.field.password}, {Auth_User_Container.field.role}, {Auth_User_Container.field.name}) VALUES(?, ?, ?, ?)'
        run_query_noreturn(auth_db_connection, query, (operator_id, operator_pass, operator_role, operator_name))
        return True

    return False


def update_operator_password(auth_db_connection: Connection, operator_id: str, operator_passwd: str) -> bool:

    query = f'UPDATE {Auth_User_Container.field.tablename} SET {Auth_User_Container.field.password} = ? WHERE {Auth_User_Container.field.username} = ?'
    return run_query_noreturn(auth_db_connection, query, (operator_passwd, operator_id))

def add_roster_to_db(person_db_connection : Connection, rid: str, name: str, start_time: str, end_time: str, offday: str) -> Union[int,bool]:
    
    query = f'SELECT * FROM {Person_Roster_Container.field.tablename} WHERE {Person_Roster_Container.field.name} = ?'
    
    res = run_fetch_query(person_db_connection, query, (name, ))
    
    if res:
        if len(res)>0:
            return -1

    query = f'INSERT INTO {Person_Roster_Container.field.tablename}({Person_Roster_Container.field.rid}, {Person_Roster_Container.field.name}, {Person_Roster_Container.field.starttime}, {Person_Roster_Container.field.endtime},{Person_Roster_Container.field.offday}) VALUES(?, ?, ?, ?, ?)'
    return run_query_noreturn(person_db_connection, query, (rid, name, start_time, end_time, offday))



def add_department_to_db(person_db_connection : Connection, deptname: str, location: str, depthod: str, timestamp: Optional[str] = str(datetimemodule.now())) -> Union[int,bool]:
    
    query = f'SELECT * FROM {Person_Department_Container.field.tablename} WHERE {Person_Department_Container.field.deptname} = ? AND {Person_Department_Container.field.location} = ?'
    
    res = run_fetch_query(person_db_connection, query, (deptname, location))
    
    if res:
        if len(res)>0:
            return -1
        
    query = f'INSERT INTO {Person_Department_Container.field.tablename}({Person_Department_Container.field.deptname},{Person_Department_Container.field.location}, {Person_Department_Container.field.depthod},{Person_Department_Container.field.timestamp}) VALUES (?,?,?,?)'
    
    return run_query_noreturn(person_db_connection, query, (deptname, location, depthod, timestamp))

def add_holiday_to_db(person_db_connection : Connection, date: str, name: str, htype: Optional[str] = "Company", deptid: Optional[str] = None) -> Union[int,bool]:
    
    
    res = select_from_holiday(person_db_connection, date = date, deptid = deptid, htype= htype, name = name)
    
    # print(res)
    if res:
        # print(3,len(res))
        if len(res)>0:
            return -1
        
    query = f'INSERT INTO {Person_Holiday_Container.field.tablename}({Person_Holiday_Container.field.date},{Person_Holiday_Container.field.name}, {Person_Holiday_Container.field.htype},{Person_Holiday_Container.field.deptid}) VALUES (?,?,?,?)'
    
    return run_query_noreturn(person_db_connection, query, (date, name, htype, deptid))

def add_location_to_db(person_db_connection: Connection, location: str, locationname: str) -> bool:
    query = f'SELECT * FROM {Person_Location_Container.field.tablename} WHERE {Person_Location_Container.field.location} = ?'
    
    res = run_fetch_query(person_db_connection, query, (location,))
    
    if res:
        if len(res)>0:
            return -1
    
    query = f'INSERT INTO {Person_Location_Container.field.tablename}({Person_Location_Container.field.location},{Person_Location_Container.field.locationname}) VALUES (?,?)'
    
    return run_query_noreturn(person_db_connection, query, (location, locationname))

def add_category_to_db(person_db_connection: Connection, name: str, cattype: Optional[str] = "Person") -> bool:
    query = f'SELECT * FROM {Person_Category_Container.field.tablename} WHERE {Person_Category_Container.field.name} = ?'
    
    res = run_fetch_query(person_db_connection, query, (name,))
    
    if res:
        if len(res)>0:
            return -1
    
    query = f'INSERT INTO {Person_Category_Container.field.tablename}({Person_Category_Container.field.name},{Person_Category_Container.field.cattype}) VALUES (?,?)'
    
    return run_query_noreturn(person_db_connection, query, (name, cattype))


def delete_holiday_from_db(person_db_connection : Connection, date: str, name: str, htype: str, deptid: Optional[str] = None) -> bool:
    
    query = f'DELETE FROM {Person_Holiday_Container.field.tablename} WHERE {Person_Holiday_Container.field.date} = ? AND {Person_Holiday_Container.field.name} = ? AND {Person_Holiday_Container.field.htype} = ?'
           
    values = None
    if deptid!=None:
        query += f' AND {Person_Holiday_Container.field.deptid} = ? '
        values = (date, name, htype, deptid)
    else:
        values = (date, name, htype)
    
    # print(query)
    return run_query_noreturn(person_db_connection, query, values)


    



 