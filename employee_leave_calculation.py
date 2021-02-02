from attendance.models import *
from core.models import *
from holidays.models import *
from pms.models.module_attendence import *
from tdms.models.module_attendence import *
from rest_framework.exceptions import APIException
import math
from django.db.models import Sum, When, Case, Value, CharField, IntegerField, F, Q
import calendar
from datetime import timedelta


def grace_calculation(joining_date, attendenceMonthMaster):
    month_start_date = attendenceMonthMaster[0]['month_start'].date()
    month_end_date = attendenceMonthMaster[0]['month_end'].date()
    # print('month_start_date',month_start_date,month_end_date)
    month_days = (month_end_date - month_start_date).days
    # print('month_days',month_days)
    remaining_days = (month_end_date - joining_date).days
    available_grace = round((remaining_days / month_days) * int(attendenceMonthMaster[0]['grace_available']))
    return available_grace


def roundCustom(net_monthly_leave, last, leave_part_2_not_cofirm):
    # print('net_monthly_leave',net_monthly_leave)
    print(last)
    round_off = net_monthly_leave
    # print('------------net_monthly leave-----------', net_monthly_leave)
    net_monthly_leave_extra = str(net_monthly_leave).split('.')[1]
    int_part = str(net_monthly_leave).split('.')[0]
    # print('net_monthly_leave_extra',net_monthly_leave_extra)
    # if last:
    #     print("---------------in last------------------------")
    #     mont_obj = AttendenceLeaveAllocatePerMonthPerUser.objects.latest('id').employee
    #     obj_lst = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee=mont_obj)
    #     print(obj_lst.count())
    #     sum = 0
    #     for each in obj_lst:
    #         sum = sum + each.round_figure_not_confirm
    #     print(sum)
    #     alloted = leave_part_2_not_cofirm
    #     print(alloted)
    #     rem_leave = float(alloted) - float(sum)
    #     print(rem_leave)
    #     des = str(rem_leave).split('.')
    #     check = float('0.'+des[1])
    #     if check < 0.3:
    #         round_off = float(des[0])+0.0
    #
    #     elif check >= 0.3 and check < 0.7:
    #         frq_add = 0.5
    #         round_off = float(des[0])+frq_add
    #     elif check >= 0.7:
    #         frq_add = 1.0
    #         round_off = float(des[0]) + frq_add
    #
    # else:
    #     des = str(net_monthly_leave).split('.')
    #     check = float('0.' + des[1])
    #     frq_add = 0.0
    #
    #     if check < 0.3:
    #         round_off = float(des[0]) + frq_add
    #     elif check >= 0.3 and check < 0.7:
    #         frq_add = 0.5
    #         round_off = float(des[0])+frq_add
    #     elif check >= 0.7:
    #         frq_add = 1.0
    #         round_off = float(des[0])+frq_add
    # print("value", value)
    if last:
        # print("---------------in last------------------------")
        mont_obj = AttendenceLeaveAllocatePerMonthPerUser.objects.latest('id').employee
        # print(each_month)
        # if each_month:
        #     obj_lst = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee=mont_obj, month__year_start_date=each_month.year_start_date)
        # else:
        obj_lst = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee=mont_obj)
        print("obj_count",obj_lst.count())
        sum = 0
        for each in obj_lst:
            sum = sum + each.round_figure_not_confirm
        # print(sum)
        alloted = leave_part_2_not_cofirm
        rem_leave = float(alloted) - float(sum)
        round_off = rem_leave
    else:
        # print("in else part")
        if '5' == net_monthly_leave_extra:
            # round_off = round_off + 0.5
            if int(int_part):
                round_off = round_off + 0.5
            else:
                round_off = 1.0

            # round_off = round_off
        else:
            round_off = round(round_off)
            # des = str(net_monthly_leave).split('.')
            # check = float('0.' + des[1])
            # frq_add = 0.0
            #
            # if check < 0.5:
            #     round_off = float(des[0]) + frq_add
            # elif check > 0.5:
            #     frq_add = 1.0
            #     round_off = float(des[0]) + frq_add



        print('round_off', round_off)
    if round_off == 0.0:
        round_off = 0.0
    # print("@@@@@@@@@@@@@@@@@@@@@", round_off)

    next_excess_or_short_leaves = round(net_monthly_leave - round_off, 1)
    # print('next_excess_or_short_leaves',next_excess_or_short_leaves)
    # print('sda',{'round_off': round_off,'next_excess_or_short_leaves': next_excess_or_short_leaves})
    print({'round_off': round_off, 'next_excess_or_short_leaves': next_excess_or_short_leaves})
    return {'round_off': round_off, 'next_excess_or_short_leaves': next_excess_or_short_leaves}


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def roundOffLeaveCalculation(users, attendenceMonthMaster, leave_part_1_confirm, leave_part_2_not_cofirm, total_days,
                             year_end_date, month_start, joining_date, cl, sl, el, al, is_joining_year=None):
    '''
        Leave Calculation on Monthly Basis [(32/365*No. Of Days in Month)]+Excess/Short Leaves in previous month
    '''
    try:

        # print("leave part 1", leave_part_1_confirm, "leave part 2 not confirm", leave_part_2_not_cofirm,
        #       "total days", total_days, "year_end_date", year_end_date, "month_start", month_start)
        # print(month_start, year_end_date)
        attendenceMonthMaster = AttendenceMonthMaster.objects.filter(month_start__date__gte=month_start,
                                                                     month_end__date__lte=year_end_date,
                                                                     is_deleted=False)

        # print('attendenceMonthMaster 1111111', attendenceMonthMaster)
        for user in users:
            # user = user.id
            for index, each_month in enumerate(attendenceMonthMaster):
                # print('index', index, type(index))
                # print("-------------------------",index)
                last = 0
                if (index + 1) == attendenceMonthMaster.count():
                    # print("in last step")
                    last = 1
                if index == 0:
                    excess_or_short_leaves_in_previous_month = 0
                    excess_or_short_leaves_in_previous_month_for_not_confirm = 0
                    excess_or_short_cl_in_previous_month = 0
                    excess_or_short_el_in_previous_month = 0
                    excess_or_short_sl_in_previous_month = 0
                    excess_or_short_al_in_previous_month = 0
                else:
                    attendenceLeaveAllocatePerMonthPerUser = AttendenceLeaveAllocatePerMonthPerUser.objects.get(
                        employee_id=user, month=(each_month.id - 1)
                    )
                    # print('attendenceLeaveAllocatePerMonthPerUser',attendenceLeaveAllocatePerMonthPerUser)
                    excess_or_short_leaves_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure)

                    excess_or_short_leaves_in_previous_month_for_not_confirm = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave_not_confirm -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure_not_confirm)

                    excess_or_short_cl_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_cl -
                            attendenceLeaveAllocatePerMonthPerUser.round_cl_allotted)
                    excess_or_short_el_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_el -
                            attendenceLeaveAllocatePerMonthPerUser.round_el_allotted)
                    excess_or_short_al_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure)
                    excess_or_short_sl_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_sl -
                            attendenceLeaveAllocatePerMonthPerUser.round_sl_allotted)

                '''
                    Actual Round Off Calculation using Total Leave for any confirm employee
                '''

                total_leave = leave_part_1_confirm / total_days
                total_cl = cl / total_days
                total_el = el / total_days
                total_sl = sl / total_days
                total_al = al / total_days
                print("--------", total_cl, total_el, total_sl)
                if not index and is_joining_year:
                    print("in index and is join year true")
                    total_leave = (total_leave * (int(each_month.days_in_month) - int(joining_date.day)))
                    # if
                    total_al = (total_al * (int(each_month.days_in_month)))
                    total_sl = (total_sl * (int(each_month.days_in_month) - int(joining_date.day)))
                    total_el = (total_el * (int(each_month.days_in_month) - int(joining_date.day)))
                    total_cl = (total_cl * (int(each_month.days_in_month) - int(joining_date.day)))
                else:
                    total_leave = (total_leave * int(each_month.days_in_month))
                    total_al = (total_al * (int(each_month.days_in_month)))
                    total_sl = (total_sl * (int(each_month.days_in_month)))
                    total_el = (total_el * (int(each_month.days_in_month)))
                    total_cl = (total_cl * (int(each_month.days_in_month)))
                # print('total_leave', total_leave)
                leave_calculation = round(total_leave, 1)
                al_calculation = round(total_al, 1)
                cl_calculation = round(total_cl, 1)
                el_calculation = round(total_el, 1)
                sl_calculation = round(total_sl, 1)
                net_monthly_leave = leave_calculation + float(
                    excess_or_short_leaves_in_previous_month)  # For First Month
                cl_monthly_leave = cl_calculation + float(excess_or_short_cl_in_previous_month)  # For First Month
                el_monthly_leave = el_calculation + float(excess_or_short_el_in_previous_month)
                sl_monthly_leave = sl_calculation + float(excess_or_short_sl_in_previous_month)
                al_monthly_leave = al_calculation + float(excess_or_short_al_in_previous_month)
                round_figure_details = roundCustom(net_monthly_leave, last, leave_part_2_not_cofirm)
                # print("in this", last)
                if last:
                    # print("hfjkdshfjdhfdsjhfdjfhdsjfhdjfhsdjfhsjfhdsfjshfjshfdhkjsfhjfhdjfh")
                    # print("in last")
                    last = 0
                    print(attendenceMonthMaster)
                    round_figure_cl_details = roundCustom(cl_monthly_leave, last, cl)
                    round_figure_el_details = roundCustom(el_monthly_leave, last, el)
                    round_figure_sl_details = roundCustom(sl_monthly_leave, last, sl)
                    # last = 0
                    round_figure_al_details = roundCustom(al_monthly_leave, last, al)
                    last = 1
                else:
                    # print("not in last")
                    round_figure_cl_details = roundCustom(cl_monthly_leave, last, cl)
                    round_figure_el_details = roundCustom(el_monthly_leave, last, el)
                    round_figure_sl_details = roundCustom(sl_monthly_leave, last, sl)
                    round_figure_al_details = roundCustom(al_monthly_leave, last, al)

                round_figure = round_figure_details['round_off']

                '''
                    Round Off Calculation using [leave_part_1] Leave for any not confirm employee
                '''
                total_leave1 = leave_part_2_not_cofirm / total_days
                total_leave1 = (total_leave1 * int(each_month.days_in_month))
                leave_cal_per_month_not_confirm = round(total_leave1, 1)
                net_monthly_leave_not_confirm = leave_cal_per_month_not_confirm + float(
                    excess_or_short_leaves_in_previous_month_for_not_confirm)  # For First Month
                round_figure_not_confirm_details = roundCustom(net_monthly_leave_not_confirm, last,
                                                               leave_part_2_not_cofirm)
                round_figure_not_confirm = round_figure_not_confirm_details['round_off']
                first_data = {
                    'employee_id': user,
                    'month': each_month,
                    'leave_cal_per_month': al_calculation,
                    'round_cl_allotted': round_figure_cl_details['round_off'],
                    'round_sl_allotted': round_figure_sl_details['round_off'],
                    'round_el_allotted': round_figure_el_details['round_off'],
                    # 'round_al_allotted': round_figure_al_details['round_off'],
                    'excess_or_short_leaves_in_previous_month': excess_or_short_al_in_previous_month,
                    "excess_or_cl_in_previous_month": excess_or_short_cl_in_previous_month,
                    "excess_or_el_in_previous_month": excess_or_short_el_in_previous_month,
                    "excess_or_sl_in_previous_month": excess_or_short_sl_in_previous_month,
                    'net_monthly_leave': al_monthly_leave,
                    'round_figure': round_figure_al_details['round_off'],
                    'leave_cal_per_month_not_confirm': al_calculation,
                    'excess_or_short_leaves_in_previous_month_for_not_confirm': excess_or_short_al_in_previous_month,
                    'net_monthly_leave_not_confirm': al_monthly_leave,
                    'round_figure_not_confirm': round_figure_al_details['round_off'],
                    'cl_allotted': cl_calculation,
                    'el_allotted': el_calculation,
                    'sl_allotted': sl_calculation,
                    'net_monthly_cl': cl_monthly_leave,
                    'net_monthly_el': el_monthly_leave,
                    'net_monthly_sl': sl_monthly_leave,
                    # 'al_allotted': al_calculation
                }
                # print(each_month)
                if AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee_id=user, month=each_month):
                    created = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee_id=user,
                                                                                    month=each_month).update(
                        leave_cal_per_month=al_calculation,
                        excess_or_short_leaves_in_previous_month=excess_or_short_al_in_previous_month,
                        net_monthly_leave=al_monthly_leave,
                        round_figure=round_figure_al_details['round_off'],
                        leave_cal_per_month_not_confirm=al_calculation,
                        excess_or_short_leaves_in_previous_month_for_not_confirm=excess_or_short_al_in_previous_month,
                        excess_or_cl_in_previous_month=excess_or_short_cl_in_previous_month,
                        excess_or_el_in_previous_month=excess_or_short_el_in_previous_month,
                        excess_or_sl_in_previous_month=excess_or_short_sl_in_previous_month,
                        net_monthly_leave_not_confirm=al_monthly_leave,
                        round_figure_not_confirm=round_figure_al_details['round_off'],
                        cl_allotted=cl_calculation,
                        el_allotted=el_calculation,
                        sl_allotted=sl_calculation,
                        # al_allotted= al_calculation,
                        round_cl_allotted=round_figure_cl_details['round_off'],
                        round_sl_allotted=round_figure_sl_details['round_off'],
                        round_el_allotted=round_figure_el_details['round_off'],
                        net_monthly_cl=cl_monthly_leave,
                        net_monthly_el=el_monthly_leave,
                        net_monthly_sl=sl_monthly_leave,
                        # round_al_allotted= round_figure_al_details['round_off']

                    )
                else:
                    cc, created = AttendenceLeaveAllocatePerMonthPerUser.objects.get_or_create(
                        **first_data
                    )

                # print("month wise updated")
                #     **first_data
                # )

    except Exception as e:
        raise APIException({
            'request_status': 0,
            'msg': e
        })

'''
    Start Leave Calculation [** If you want to edit then please check first then edit]
    Author :: Last modified by @Rupam Hazra [2021-01-19]
'''
def all_leave_calculation_upto_applied_date_tdms(date_object=None, user=None):
        from django.db.models import Sum

        '''
        Start :: Normal leave availed by user
        '''

        sl_eligibility = 0
        el_eligibility = 0
        cl_eligibility = 0

        month_master=AttendenceMonthMaster.objects.filter(
            month_start__date__lte=date_object,
            month_end__date__gte=date_object,
            is_deleted=False
            ).first()

        carry_forward_al = 0.0
        if user.salary_type and (user.salary_type.st_code=='FF' or user.salary_type.st_code=='EE'):
            # carry forward Leaves
            carry_forward_leave = get_carryForwardLeave(user,month_master)
            carry_forward_al = carry_forward_leave.leave_balance
        
        # taken leave from my attendance     
        availed_al,availed_ab,availed_cl,availed_el,availed_sl,availed_hd_al,availed_hd_ab,availed_hd_cl,availed_hd_el,availed_hd_sl = get_takenLeaveFromMyAttendance(month_master,date_object,user,module='TDMS')
        
        '''
            Get total leave allocation(monthly) by request start and end date
        '''
        leave_allocation_per_month = 0.0
        leave_allocation_per_month_cl = 0.0
        leave_allocation_per_month_sl = 0.0
        leave_allocation_per_month_el = 0.0

        leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
            (
                Q(month__month_start__date__gte=month_master.year_start_date.date(),month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,month__month_end__date__gte=date_object)
            ),employee=user.cu_user)

        if user.salary_type and leave_allocation_per_month_d:

            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
                leave_allocation_per_month = leave_allocation_per_month_d.aggregate(Sum('round_figure'))['round_figure__sum']

            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
                leave_allocation_per_month_sl = leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum']
            
            if user.salary_type.st_code == 'BB':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
        
            if user.salary_type.st_code == 'AA':
                leave_allocation_per_month_cl = 0
                leave_allocation_per_month_el = 0
                leave_allocation_per_month_sl = 0
                leave_allocation_per_month = 0
                
        else:
            leave_allocation_per_month_cl = 0
            leave_allocation_per_month_el = 0
            leave_allocation_per_month_sl = 0
            leave_allocation_per_month = 0.0


        print('leave_allocation_per_month',leave_allocation_per_month)           

        # advance Leave
        advance_al,advance_ab,advance_el,advance_cl = get_advanceLeaveDetails(month_master,date_object,user,module='TDMS')
        

        '''
            Section for count total leave count which means 
            total of advance leaves and approval leave
        '''
        
        total_availed_al=float(availed_al) + float(advance_al) + float(availed_hd_al/2)
        total_availed_ab=float(availed_ab) + float(advance_ab) + float(availed_hd_ab/2)
        total_availed_cl=float(availed_cl) + float(advance_cl) + float(availed_hd_cl/2)
        total_availed_el=float(availed_el) + float(advance_el) + float(availed_hd_el/2)
        total_availed_sl=float(availed_sl) + float(availed_hd_sl/2)

        # print("total_availed_al",total_availed_al)
        # print('total_availed_ab', total_availed_ab)

        '''
            Section for remaining leaves from granted leave - availed leave
        '''

        leave_allocation_per_month  = float(leave_allocation_per_month) + float(carry_forward_al)
        balance_al = leave_allocation_per_month - float(total_availed_al)
        balance_cl = float(leave_allocation_per_month_cl) - float(total_availed_cl)
        balance_sl = float(leave_allocation_per_month_sl) - float(total_availed_sl)
        balance_el = float(leave_allocation_per_month_el) - float(total_availed_el)


        availed_grace = PmsAttandanceDeviation.objects.filter(Q(attandance__employee=user.cu_user) &
                                                                Q(from_time__gte=month_master.month_start) &
                                                                Q(from_time__lte=month_master.month_end) &
                                                                Q(is_requested=True)).aggregate(Sum('duration'))['duration__sum']

        availed_grace = availed_grace if availed_grace else 0
        total_month_grace = month_master.grace_available
        grace_balance = total_month_grace - availed_grace

        
        yearly_leave_allocation = float(user.granted_cl) + float(user.granted_sl) + float(user.granted_el) + float(carry_forward_al)
        sl_eligibility = float(user.granted_sl)
        el_eligibility = float(user.granted_el)
        cl_eligibility = float(user.granted_cl)


        month_start = month_master.month_start
        if user.joining_date > month_master.year_start_date:
            approved_leave=JoiningApprovedLeave.objects.filter(employee=user.cu_user,is_deleted=False).first()
            if approved_leave:
                yearly_leave_allocation = float(approved_leave.granted_leaves_cl_sl) + float(approved_leave.el)
                sl_eligibility = float(approved_leave.sl)
                el_eligibility = float(approved_leave.el)
                cl_eligibility = float(approved_leave.cl)

                if month_master.month==approved_leave.month:    #for joining month only
                    total_month_grace=approved_leave.first_grace
                    month_start=user.joining_date
                    grace_balance=total_month_grace - availed_grace

        # START :: Flexi Hour Calculation #   
        
        total_hours_1st, working_hours_1st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=month_master.month_start, end_date=month_master.fortnight_date)
        #print('total_hours_1st',total_hours_1st,'working_hours_1st',working_hours_1st)
        #time.sleep(10)
        #print('total_hours_1st',total_hours_1st)

        ''' 
            Start Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
        '''

        total_hours_1st = (float(total_hours_1st) - float(480)) if month_master.payroll_month == 'AUGUST' else total_hours_1st

        ''' 
            End Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
        '''
        
        total_hrs_1st, total_mins_1st = divmod(int(total_hours_1st), 60)
        total_hrs_mins_1st = '{} hrs {} mins'.format(total_hrs_1st, total_mins_1st) if total_hrs_1st else '{} mins'.format(total_mins_1st)
        working_hrs_1st, working_mins_1st = divmod(int(working_hours_1st), 60)
        #print('working_mins_1st',working_hrs_1st,working_mins_1st)
        working_hrs_mins_1st = '{} hrs {} mins'.format(working_hrs_1st, working_mins_1st) if working_hrs_1st else '{} mins'.format(working_mins_1st)
     
        
        total_hours_2st, working_hours_2st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=month_master.fortnight_date + timedelta(days=1), end_date=month_master.month_end)
        #print('total_hours_2st',total_hours_2st,'working_hours_2st',working_hours_2st)
        total_hrs_2st, total_mins_2st = divmod(int(total_hours_2st), 60)
        total_hrs_mins_2st = '{} hrs {} mins'.format(total_hrs_2st, total_mins_2st) if total_hrs_2st else '{} mins'.format(total_mins_2st)
        working_hrs_2st, working_mins_2st = divmod(int(working_hours_2st), 60)
        working_hrs_mins_2st = '{} hrs {} mins'.format(working_hrs_2st, working_mins_2st) if working_hrs_2st else '{} mins'.format(working_mins_2st)
       

        fortnight = [
            {
                'fortnight': 1,
                'is_active': date_object <= month_master.fortnight_date.date(),
                'flexi_start_date': month_master.month_start,
                'flexi_end_date': month_master.fortnight_date,
                'total_hours': total_hrs_mins_1st,
                'working_hours': working_hrs_mins_1st,
                #'leave_deduction_1st':leave_deduction_1st
            },
            {
                'fortnight': 2,
                'is_active': date_object > month_master.fortnight_date.date(),
                'flexi_start_date': month_master.fortnight_date + timedelta(days=1),
                'flexi_end_date': month_master.month_end,
                'total_hours': total_hrs_mins_2st,
                'working_hours': working_hrs_mins_2st,
                #'leave_deduction_2st':leave_deduction_2st
            }
        ]
        
        # END :: Flexi Hour Calculation #


        ## Leave Decution Calculation Before Fortnight deduction ##

        total_available_balance_before_deduction = balance_al
        total_available_cl_before_deduction = balance_cl
        total_available_el_before_deduction = balance_el
        total_available_sl_before_deduction = balance_sl

        ## Leave Decution Calculation Before Fortnight deduction ##

        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##
        
        al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction = get_fortnight_leave_deduction_count(month_master,date_object,employee=user.cu_user)

        if user.salary_type:
            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
               
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
                
                balance_al =  balance_al - al_deduction
                total_availed_al += al_deduction
                total_availed_ab += ab_deduction
            
            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0

                balance_cl =  balance_cl - cl_deduction
                total_availed_cl += cl_deduction

                balance_el =  balance_el - el_deduction
                total_availed_el += el_deduction

                balance_sl =  balance_sl - sl_deduction
                total_availed_sl += sl_deduction

                total_availed_ab += ab_deduction

            if user.salary_type.st_code == 'BB':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0

                balance_cl =  balance_cl - cl_deduction
                total_availed_cl += al_deduction

                balance_el =  balance_el - el_deduction
                total_availed_el += el_deduction

                total_availed_ab += ab_deduction

            if user.salary_type.st_code == 'AA':
                total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
                total_availed_ab += ab_deduction
        else:
            total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
            total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
            total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
            total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
            total_availed_ab += ab_deduction        
        
        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##

        result = {
            "employee_id":user.cu_user.id,
            "employee_username":user.cu_user.username,
            "month_start":month_start,
            "month_end":month_master.month_end,
            "year_start":month_master.year_start_date,
            "year_end":month_master.year_end_date,
            "is_confirm": False,
            "salary_type_code": user.salary_type.st_code if user.salary_type else "",
            "salary_type": user.salary_type.st_name if user.salary_type else "",
            
            "total_available_balance_before_deduction": total_available_balance_before_deduction,
            "total_available_cl_before_deduction": total_available_cl_before_deduction,
            "total_available_el_before_deduction": total_available_el_before_deduction,
            "total_available_sl_before_deduction": total_available_sl_before_deduction,

            "total_absent": total_availed_ab,
            "fortnight": fortnight,

            "total_eligibility": yearly_leave_allocation,
            "total_accumulation": leave_allocation_per_month,
            "total_consumption": total_availed_al,
            "total_available_balance": balance_al,

            "cl_eligibility":cl_eligibility,
            "granted_cl":leave_allocation_per_month_cl,
            "availed_cl":total_availed_cl,
            "cl_balance":balance_cl if balance_cl > 0 else 0.0,

            "el_eligibility":el_eligibility,
            "granted_el":leave_allocation_per_month_el,
            "availed_el":total_availed_el,
            "el_balance":balance_el if balance_el > 0 else 0.0,

            "sl_eligibility":sl_eligibility,
            "granted_sl":leave_allocation_per_month_sl,
            "availed_sl":total_availed_sl,
            "sl_balance": balance_sl if  balance_sl > 0 else 0.0,
            }

        return result

def all_leave_calculation_upto_applied_date_pms(date_object=None, user=None):
        from django.db.models import Sum

        '''
        Start :: Normal leave availed by user
        '''

        sl_eligibility = 0
        el_eligibility = 0
        cl_eligibility = 0

        month_master=AttendenceMonthMaster.objects.filter(
            month_start__date__lte=date_object,
            month_end__date__gte=date_object,
            is_deleted=False
            ).first()

        carry_forward_al = 0.0
        if user.salary_type and (user.salary_type.st_code=='FF' or user.salary_type.st_code=='EE'):
            # carry forward Leaves
            carry_forward_leave = get_carryForwardLeave(user,month_master)
            carry_forward_al = carry_forward_leave.leave_balance if carry_forward_leave else 0
        
        # taken leave from my attendance     
        availed_al,availed_ab,availed_cl,availed_el,availed_sl,availed_hd_al,availed_hd_ab,availed_hd_cl,availed_hd_el,availed_hd_sl = get_takenLeaveFromMyAttendance(month_master,date_object,user,module='PMS')
        
        '''
            Get total leave allocation(monthly) by request start and end date
        '''
        leave_allocation_per_month = 0.0
        leave_allocation_per_month_cl = 0.0
        leave_allocation_per_month_sl = 0.0
        leave_allocation_per_month_el = 0.0

        leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
            (
                Q(month__month_start__date__gte=month_master.year_start_date.date(),month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,month__month_end__date__gte=date_object)
            ),employee=user.cu_user)

        if user.salary_type and leave_allocation_per_month_d:

            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
                leave_allocation_per_month = leave_allocation_per_month_d.aggregate(Sum('round_figure'))['round_figure__sum']

            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
                leave_allocation_per_month_sl = leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum']
            
            if user.salary_type.st_code == 'BB':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
        
            if user.salary_type.st_code == 'AA':
                leave_allocation_per_month_cl = 0
                leave_allocation_per_month_el = 0
                leave_allocation_per_month_sl = 0
                leave_allocation_per_month = 0
                
        else:
            leave_allocation_per_month_cl = 0
            leave_allocation_per_month_el = 0
            leave_allocation_per_month_sl = 0
            leave_allocation_per_month = 0.0


        print('leave_allocation_per_month',leave_allocation_per_month)           

        # advance Leave
        advance_al,advance_ab,advance_el,advance_cl = get_advanceLeaveDetails(month_master,date_object,user,module='PMS')
        

        '''
            Section for count total leave count which means 
            total of advance leaves and approval leave
        '''
        
        total_availed_al=float(availed_al) + float(advance_al) + float(availed_hd_al/2)
        total_availed_ab=float(availed_ab) + float(advance_ab) + float(availed_hd_ab/2)
        total_availed_cl=float(availed_cl) + float(advance_cl) + float(availed_hd_cl/2)
        total_availed_el=float(availed_el) + float(advance_el) + float(availed_hd_el/2)
        total_availed_sl=float(availed_sl) + float(availed_hd_sl/2)

        # print("total_availed_al",total_availed_al)
        # print('total_availed_ab', total_availed_ab)

        '''
            Section for remaining leaves from granted leave - availed leave
        '''

        leave_allocation_per_month  = float(leave_allocation_per_month) + float(carry_forward_al)
        balance_al = leave_allocation_per_month - float(total_availed_al)
        balance_cl = float(leave_allocation_per_month_cl) - float(total_availed_cl)
        balance_sl = float(leave_allocation_per_month_sl) - float(total_availed_sl)
        balance_el = float(leave_allocation_per_month_el) - float(total_availed_el)


        availed_grace = PmsAttandanceDeviation.objects.filter(Q(attandance__employee=user.cu_user) &
                                                                Q(from_time__gte=month_master.month_start) &
                                                                Q(from_time__lte=month_master.month_end) &
                                                                Q(is_requested=True)).aggregate(Sum('duration'))['duration__sum']

        availed_grace = availed_grace if availed_grace else 0
        total_month_grace = month_master.grace_available
        grace_balance = total_month_grace - availed_grace

        
        yearly_leave_allocation = float(user.granted_cl) + float(user.granted_sl) + float(user.granted_el) + float(carry_forward_al)
        sl_eligibility = float(user.granted_sl)
        el_eligibility = float(user.granted_el)
        cl_eligibility = float(user.granted_cl)


        month_start = month_master.month_start
        if user.joining_date > month_master.year_start_date:
            approved_leave=JoiningApprovedLeave.objects.filter(employee=user.cu_user,is_deleted=False).first()
            if approved_leave:
                yearly_leave_allocation = float(approved_leave.granted_leaves_cl_sl) + float(approved_leave.el)
                sl_eligibility = float(approved_leave.sl)
                el_eligibility = float(approved_leave.el)
                cl_eligibility = float(approved_leave.cl)

                if month_master.month==approved_leave.month:    #for joining month only
                    total_month_grace=approved_leave.first_grace
                    month_start=user.joining_date
                    grace_balance=total_month_grace - availed_grace

        # START :: Flexi Hour Calculation #   
        
        total_hours_1st, working_hours_1st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=month_master.month_start, end_date=month_master.fortnight_date)
        #print('total_hours_1st',total_hours_1st,'working_hours_1st',working_hours_1st)
        #time.sleep(10)
        #print('total_hours_1st',total_hours_1st)

        ''' 
            Start Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
        '''

        total_hours_1st = (float(total_hours_1st) - float(480)) if month_master.payroll_month == 'AUGUST' else total_hours_1st

        ''' 
            End Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
        '''
        
        total_hrs_1st, total_mins_1st = divmod(int(total_hours_1st), 60)
        total_hrs_mins_1st = '{} hrs {} mins'.format(total_hrs_1st, total_mins_1st) if total_hrs_1st else '{} mins'.format(total_mins_1st)
        working_hrs_1st, working_mins_1st = divmod(int(working_hours_1st), 60)
        #print('working_mins_1st',working_hrs_1st,working_mins_1st)
        working_hrs_mins_1st = '{} hrs {} mins'.format(working_hrs_1st, working_mins_1st) if working_hrs_1st else '{} mins'.format(working_mins_1st)
     
        
        total_hours_2st, working_hours_2st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=month_master.fortnight_date + timedelta(days=1), end_date=month_master.month_end)
        #print('total_hours_2st',total_hours_2st,'working_hours_2st',working_hours_2st)
        total_hrs_2st, total_mins_2st = divmod(int(total_hours_2st), 60)
        total_hrs_mins_2st = '{} hrs {} mins'.format(total_hrs_2st, total_mins_2st) if total_hrs_2st else '{} mins'.format(total_mins_2st)
        working_hrs_2st, working_mins_2st = divmod(int(working_hours_2st), 60)
        working_hrs_mins_2st = '{} hrs {} mins'.format(working_hrs_2st, working_mins_2st) if working_hrs_2st else '{} mins'.format(working_mins_2st)
       

        fortnight = [
            {
                'fortnight': 1,
                'is_active': date_object <= month_master.fortnight_date.date(),
                'flexi_start_date': month_master.month_start,
                'flexi_end_date': month_master.fortnight_date,
                'total_hours': total_hrs_mins_1st,
                'working_hours': working_hrs_mins_1st,
                #'leave_deduction_1st':leave_deduction_1st
            },
            {
                'fortnight': 2,
                'is_active': date_object > month_master.fortnight_date.date(),
                'flexi_start_date': month_master.fortnight_date + timedelta(days=1),
                'flexi_end_date': month_master.month_end,
                'total_hours': total_hrs_mins_2st,
                'working_hours': working_hrs_mins_2st,
                #'leave_deduction_2st':leave_deduction_2st
            }
        ]
        
        # END :: Flexi Hour Calculation #


        ## Leave Decution Calculation Before Fortnight deduction ##

        total_available_balance_before_deduction = balance_al
        total_available_cl_before_deduction = balance_cl
        total_available_el_before_deduction = balance_el
        total_available_sl_before_deduction = balance_sl

        ## Leave Decution Calculation Before Fortnight deduction ##

        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##
        
        al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction = get_fortnight_leave_deduction_count(month_master,date_object,employee=user.cu_user)

        if user.salary_type:
            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
               
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
                
                balance_al =  balance_al - al_deduction
                total_availed_al += al_deduction
                total_availed_ab += ab_deduction
            
            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0

                balance_cl =  balance_cl - cl_deduction
                total_availed_cl += cl_deduction

                balance_el =  balance_el - el_deduction
                total_availed_el += el_deduction

                balance_sl =  balance_sl - sl_deduction
                total_availed_sl += sl_deduction

                total_availed_ab += ab_deduction

            if user.salary_type.st_code == 'BB':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0

                balance_cl =  balance_cl - cl_deduction
                total_availed_cl += cl_deduction

                balance_el =  balance_el - el_deduction
                total_availed_el += el_deduction

                total_availed_ab += ab_deduction

            if user.salary_type.st_code == 'AA':
                total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
                total_availed_ab += ab_deduction
        else:
            total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
            total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
            total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
            total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
            total_availed_ab += ab_deduction        
        
        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##

        result = {
            "employee_id":user.cu_user.id,
            "employee_username":user.cu_user.username,
            "month_start":month_start,
            "month_end":month_master.month_end,
            "year_start":month_master.year_start_date,
            "year_end":month_master.year_end_date,
            "is_confirm": False,
            "salary_type_code": user.salary_type.st_code if user.salary_type else "",
            "salary_type": user.salary_type.st_name if user.salary_type else "",
            
            "total_available_balance_before_deduction": total_available_balance_before_deduction,
            "total_available_cl_before_deduction": total_available_cl_before_deduction,
            "total_available_el_before_deduction": total_available_el_before_deduction,
            "total_available_sl_before_deduction": total_available_sl_before_deduction,

            "total_absent": total_availed_ab,
            "fortnight": fortnight,

            "total_eligibility": yearly_leave_allocation,
            "total_accumulation": leave_allocation_per_month,
            "total_consumption": total_availed_al,
            "total_available_balance": balance_al,

            "cl_eligibility":cl_eligibility,
            "granted_cl":leave_allocation_per_month_cl,
            "availed_cl":total_availed_cl,
            "cl_balance":balance_cl if balance_cl > 0 else 0.0,

            "el_eligibility":el_eligibility,
            "granted_el":leave_allocation_per_month_el,
            "availed_el":total_availed_el,
            "el_balance":balance_el if balance_el > 0 else 0.0,

            "sl_eligibility":sl_eligibility,
            "granted_sl":leave_allocation_per_month_sl,
            "availed_sl":total_availed_sl,
            "sl_balance": balance_sl if  balance_sl > 0 else 0.0,
            }

        return result

def all_leave_calculation_upto_applied_date(date_object=None, user=None):

        '''
            Author :: Last modified by Rupam Hazra
            Note :: Leave calculation = [
                        carry forward Leaves + 
                        taken leave from my attendance + 
                        advance Leave + 
                        fortnight Leave for PMS +
                        fortnight Leave for PMS to HRMS Transfer
                    ] As per salary type
        '''

        from django.db.models import Sum

        '''
            Start :: Normal leave availed by user
        '''

        sl_eligibility = 0
        el_eligibility = 0
        cl_eligibility = 0
        module='HRMS'

        month_master=AttendenceMonthMaster.objects.filter(
            month_start__date__lte=date_object,month_end__date__gte=date_object,is_deleted=False).first()

        carry_forward_al = 0.0
        if user.salary_type and (user.salary_type.st_code=='FF' or user.salary_type.st_code=='EE'):
            # carry forward Leaves
            carry_forward_leave = get_carryForwardLeave(user,month_master)
            carry_forward_al = carry_forward_leave.leave_balance if carry_forward_leave else 0.0

        # taken leave from my attendance     
        availed_al,availed_ab,availed_cl,availed_el,availed_sl,availed_hd_al,availed_hd_ab,availed_hd_cl,availed_hd_el,availed_hd_sl = get_takenLeaveFromMyAttendance(month_master,date_object,user,module)

        '''
            Get total leave allocation(monthly) by request start and end date
        '''
        leave_allocation_per_month = 0.0
        leave_allocation_per_month_cl = 0.0
        leave_allocation_per_month_sl = 0.0
        leave_allocation_per_month_el = 0.0

        leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
            (
                Q(month__month_start__date__gte=month_master.year_start_date.date(),month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,month__month_end__date__gte=date_object)
            ),employee=user.cu_user)
            
        month_wise_leave = list()
        if user.salary_type and leave_allocation_per_month_d:

            month_wise_leave = get_monthlyAccumulation(leave_allocation_per_month_d)

            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
                leave_allocation_per_month = leave_allocation_per_month_d.aggregate(Sum('round_figure'))['round_figure__sum']
                
            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                #print('round_cl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum'])
                #print('round_el_allotted',leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum'])
                #print('round_sl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum'])
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
                leave_allocation_per_month_sl = leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum']

            
            if user.salary_type.st_code == 'BB':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
        
            if user.salary_type.st_code == 'AA':
                leave_allocation_per_month_cl = 0
                leave_allocation_per_month_el = 0
                leave_allocation_per_month_sl = 0
                leave_allocation_per_month = 0
                
        else:
            leave_allocation_per_month_cl = 0
            leave_allocation_per_month_el = 0
            leave_allocation_per_month_sl = 0
            leave_allocation_per_month = 0.0

        # advance Leave
        advance_al,advance_ab,advance_el,advance_cl = get_advanceLeaveDetails(month_master,date_object,user,module)

        '''
            Section for count total leave count which means 
            total of advance leaves and approval leave
        '''

        total_availed_al=float(availed_al)+float(advance_al)+float(availed_hd_al/2)
        total_availed_ab=float(availed_ab) + float(advance_ab) +float(availed_hd_ab/2)
        total_availed_cl=float(availed_cl) + float(advance_cl) +float(availed_hd_cl/2)
        total_availed_el=float(availed_el) + float(advance_el) +float(availed_hd_el/2)
        total_availed_sl=float(availed_sl) + float(availed_hd_sl/2)

        #print("total_availed_al",total_availed_al)
        #print('total_availed_sl', total_availed_sl)

        '''
            Section for remaining leaves from granted leave - availed leave
        '''
        leave_allocation_per_month  = float(leave_allocation_per_month) + float(carry_forward_al)
        balance_al = leave_allocation_per_month - float(total_availed_al)
        balance_cl = float(leave_allocation_per_month_cl) - float(total_availed_cl)
        balance_sl = float(leave_allocation_per_month_sl) - float(total_availed_sl)
        balance_el = float(leave_allocation_per_month_el) - float(total_availed_el)

        if module == 'PMS':
            availed_grace = PmsAttandanceDeviation.objects.filter(Q(attandance__employee=user.cu_user) &
                                                                    Q(from_time__gte=month_master.month_start) &
                                                                    Q(from_time__lte=month_master.month_end) &
                                                                    Q(is_requested=True)).aggregate(Sum('duration'))['duration__sum']
        else:
            availed_grace = AttendanceApprovalRequest.objects.filter(Q(attendance__employee=user.cu_user) &
                                                                    Q(duration_start__gte=month_master.month_start) &
                                                                    Q(duration_start__lte=month_master.month_end) &
                                                                    Q(is_requested=True) & Q(is_deleted=False) &
                                                                    (Q(request_type='GR')|Q(checkin_benchmark=True))
                                                                    ).aggregate(Sum('duration'))['duration__sum']

        availed_grace = availed_grace if availed_grace else 0
        total_month_grace = month_master.grace_available
        grace_balance = total_month_grace - availed_grace

        yearly_leave_allocation = float(user.granted_cl) + float(user.granted_sl) + float(user.granted_el) + float(carry_forward_al)
        sl_eligibility = float(user.granted_sl)
        el_eligibility = float(user.granted_el)
        cl_eligibility = float(user.granted_cl)

        
        month_start = month_master.month_start
        
        if user.joining_date > month_master.year_start_date:
            approved_leave=JoiningApprovedLeave.objects.filter(employee=user.cu_user,is_deleted=False).first()
            if approved_leave:
                yearly_leave_allocation = float(approved_leave.cl) + float(approved_leave.sl) + float(approved_leave.el)

                sl_eligibility = float(approved_leave.sl)
                el_eligibility = float(approved_leave.el)
                cl_eligibility = float(approved_leave.cl)

                if month_master.month==approved_leave.month:    #for joining month only
                    total_month_grace=approved_leave.first_grace
                    month_start=user.joining_date
                    grace_balance=total_month_grace - availed_grace

        
        total_available_balance_before_deduction = balance_al
        total_available_cl_before_deduction = balance_cl
        total_available_el_before_deduction = balance_el
        total_available_sl_before_deduction = balance_sl
        total_available_ab_before_deduction = total_availed_ab

        ## Leave Decution Calculation from PmsAttandanceLeaveBalanceTransferLog table ##

        transfer_al_deduction,transfer_ab_deduction,transfer_cl_deduction,transfer_el_deduction,transfer_sl_deduction = get_pmsAttandanceLeaveBalanceTransferLog(
            month_master,date_object,employee=user.cu_user)

        transfer_availed_al = transfer_al_deduction
        transfer_availed_ab = transfer_ab_deduction
        transfer_availed_cl = transfer_cl_deduction
        transfer_availed_el = transfer_el_deduction
        transfer_availed_sl = transfer_sl_deduction

        balance_al =  balance_al - transfer_al_deduction
        total_availed_al += transfer_al_deduction
        
        balance_cl =  balance_cl - transfer_cl_deduction
        total_availed_cl += transfer_cl_deduction

        balance_el =  balance_el - transfer_el_deduction
        total_availed_el += transfer_el_deduction

        balance_sl =  balance_sl - transfer_sl_deduction
        total_availed_sl += transfer_sl_deduction

        total_availed_ab += transfer_ab_deduction
                   
        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##

        al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction = get_fortnight_leave_deduction_count(
            month_master,date_object,employee=user.cu_user)

        fortnight_availed_al = al_deduction
        fortnight_availed_cl = cl_deduction
        fortnight_availed_el = el_deduction
        fortnight_availed_sl = sl_deduction
        fortnight_availed_ab = ab_deduction

        balance_al =  balance_al - al_deduction
        total_availed_al += al_deduction

        balance_cl =  balance_cl - cl_deduction
        total_availed_cl += cl_deduction

        balance_el =  balance_el - el_deduction
        total_availed_el += el_deduction

        balance_sl =  balance_sl - sl_deduction
        total_availed_sl += sl_deduction

        total_availed_ab += ab_deduction

        ## Leave Decution Calculation from PmsAttandanceFortnightLeaveDeductionLog table ##


        if user.salary_type:
            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
               
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
                
                balance_al =  balance_al
                total_availed_al = total_availed_al
            
            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0

                balance_cl =  balance_cl
                total_availed_cl = total_availed_cl

                balance_el =  balance_el
                total_availed_el = total_availed_el

                balance_sl =  balance_sl
                total_availed_sl = total_availed_sl

            if user.salary_type.st_code == 'BB':
                yearly_leave_allocation = total_availed_al = balance_al = total_available_balance_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0

                balance_cl =  balance_cl
                total_availed_cl = total_availed_cl

                balance_el =  balance_el
                total_availed_el = total_availed_el

            if user.salary_type.st_code == 'AA':
                total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
                total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
                total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
                total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
        else:
            total_availed_al = balance_al = yearly_leave_allocation = total_available_balance_before_deduction = 0
            total_availed_cl = balance_cl = cl_eligibility = total_available_cl_before_deduction = 0
            total_availed_el = balance_el = el_eligibility = total_available_el_before_deduction = 0
            total_availed_sl = balance_sl = sl_eligibility = total_available_sl_before_deduction = 0
      
        
        monthly_od_duration, monthly_od_count = get_monthlyODdetails(month_master,date_object,user)

        result = {
            "month_start":month_start,
            "month_end":month_master.month_end,
            "year_start":month_master.year_start_date,
            "year_end":month_master.year_end_date,
            "is_confirm": False,
            "total_month_grace": total_month_grace,
            "availed_grace": availed_grace,
            "grace_balance": grace_balance,
            "salary_type_code": user.salary_type.st_code if user.salary_type else "",
            "salary_type": user.salary_type.st_name if user.salary_type else "",
            "carry_leaves": carry_forward_al,
            
            "monthly_od_count": monthly_od_count,
            "monthly_od_duration": monthly_od_duration,

            "advance_leave_al":advance_al,
            "advance_leave_ab":advance_ab,
            "advance_leave_cl":advance_cl,
            "advance_leave_el":advance_el,


            "total_available_balance_before_deduction": total_available_balance_before_deduction,
            "total_available_ab_before_deduction": total_available_ab_before_deduction,
            "total_available_cl_before_deduction": total_available_cl_before_deduction,
            "total_available_el_before_deduction": total_available_el_before_deduction,
            "total_available_sl_before_deduction": total_available_sl_before_deduction,

            "transfer_availed_al":transfer_availed_al,
            "transfer_availed_ab":transfer_availed_ab,
            "transfer_availed_cl":transfer_availed_cl,
            "transfer_availed_el":transfer_availed_el,
            "transfer_availed_sl":transfer_availed_sl,
            

            "fortnight_availed_al":fortnight_availed_al,
            "fortnight_availed_ab":fortnight_availed_ab,
            "fortnight_availed_cl":fortnight_availed_cl,
            "fortnight_availed_el":fortnight_availed_el,
            "fortnight_availed_sl":fortnight_availed_sl,
            

            "total_absent": total_availed_ab,

            "total_eligibility": yearly_leave_allocation,
            "total_accumulation": leave_allocation_per_month,
            "total_consumption": total_availed_al,
            "total_available_balance": balance_al,

            "cl_eligibility":cl_eligibility,
            "granted_cl":leave_allocation_per_month_cl,
            "availed_cl":total_availed_cl,
            "cl_balance":balance_cl if balance_cl > 0 else 0.0,

            "el_eligibility":el_eligibility,
            "granted_el":leave_allocation_per_month_el,
            "availed_el":total_availed_el,
            "el_balance":balance_el if balance_el > 0 else 0.0,

            "sl_eligibility":sl_eligibility,
            "granted_sl":leave_allocation_per_month_sl,
            "availed_sl":total_availed_sl,
            "sl_balance": balance_sl if  balance_sl > 0 else 0.0,

            "monthly_accumulation":month_wise_leave,
            
            }

        return result

def get_monthlyAccumulation(leave_allocation_per_month_d):
    month_wise_leave = list()
    monthDict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep',10: 'Oct', 11: 'Nov', 12: 'Dec'}
    for each in leave_allocation_per_month_d:
        temp_month_data = dict()
        temp_month_data["accumulation"] = int(each.round_figure)
        temp_month_data["cl"] = int(each.round_cl_allotted)
        temp_month_data["sl"] = int(each.round_el_allotted)
        temp_month_data["el"] = int(each.round_sl_allotted)
        temp_month_data["month"] = monthDict[each.month.month]

        month_wise_leave.append(temp_month_data)
    return month_wise_leave

def get_carryForwardLeave(user,month_master):
    year_start = str(month_master.year_start_date.year - 1) + '-04-01'
    year_end = str(month_master.year_end_date.year - 1) +'-03-31'
    carry_forward_leave = AttendanceCarryForwardLeaveBalanceYearly.objects.filter(
                    employee=user.cu_user, 
                    is_deleted=False,
                    year_start_date__date = year_start,
                    year_end_date__date = year_end
                    )
    #print('carry_forward_leave',carry_forward_leave)
    #print('carry_forward_leave',carry_forward_leave.query)
    return carry_forward_leave.first()

def get_takenLeaveFromMyAttendance(month_master,date_object=None,user=None,module='HRMS'):

    availed_hd_ab = 0.0
    availed_hd_al = 0.0
    availed_hd_cl = 0.0
    availed_hd_sl = 0.0
    availed_hd_el = 0.0

    availed_ab = 0.0
    availed_al = 0.0
    availed_cl = 0.0
    availed_el = 0.0
    availed_sl = 0.0

    if module == 'PMS':
        attendence_daily_data = PmsAttandanceDeviation.objects.filter(((
            Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
            (Q(leave_type_changed_period__isnull=True)&(Q(deviation_type='FD')|Q(deviation_type='HD')))),
            from_time__date__gte=month_master.year_start_date.date(),
            attandance__employee=user.cu_user.id,is_requested=True).values('from_time__date').distinct()
        
        date_list = [x['from_time__date'] for x in attendence_daily_data.iterator()]
        
        availed_master_wo_reject_fd = PmsAttandanceDeviation.objects.\
            filter((Q(approved_status=1)|Q(approved_status=2)|Q(approved_status=3)),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attandance__employee=user.cu_user.id,
                    attandance__date__date__in=date_list,is_requested=True).annotate(
                        leave_type_final = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='FD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    leave_type_final_hd = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='HD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    ).values('leave_type_final','leave_type_final_hd','attandance__date__date').distinct()
        if availed_master_wo_reject_fd:
            for data in date_list:
                availed_FD=availed_master_wo_reject_fd.filter(attandance__date__date=data)
                #print('availed_FD',availed_FD)
                if availed_FD.filter(leave_type_final__isnull=False):
                    if availed_FD.values('leave_type_final').count() >1:
                        if availed_FD.filter(leave_type_final='AB'):
                            availed_ab=availed_ab+1.0
                        elif availed_FD.filter(leave_type_final='AL'):
                            availed_al = availed_al + 1.0
                        elif availed_FD.filter(leave_type_final='EL'):
                            availed_el = availed_el + 1.0
                        elif availed_FD.filter(leave_type_final='SL'):
                            availed_sl = availed_sl + 1.0
                        elif availed_FD.filter(leave_type_final='CL'):
                            availed_cl = availed_cl + 1.0    
                    else:
                        l_type=availed_FD[0]['leave_type_final']
                        if l_type == 'AL':
                            availed_al = availed_al + 1.0
                        elif l_type == 'AB':
                            availed_ab=availed_ab+1.0
                        elif l_type == 'EL':
                            availed_el=availed_el+1.0
                        elif l_type == 'SL':
                            availed_sl=availed_sl+1.0
                        elif l_type == 'CL':
                            availed_cl=availed_cl+1.0

                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    #print('saddsadsdasdasdasdsadsadsdasdasdad')
                    #print('leave_type_final_hd', availed_FD.values('leave_type_final_hd').count())
                    #time.sleep(10)
                    if availed_FD.values('leave_type_final_hd').count() >1:
                        if availed_FD.filter(leave_type_final_hd='AB'):
                            availed_hd_ab=availed_hd_ab+1.0
                        elif availed_FD.filter(leave_type_final_hd='AL'):
                            availed_hd_al=availed_hd_al+1.0
                        elif availed_FD.filter(leave_type_final_hd='CL'):
                            availed_hd_cl=availed_hd_cl+1.0
                        elif availed_FD.filter(leave_type_final_hd='EL'):
                            availed_hd_el=availed_hd_el+1.0
                        elif availed_FD.filter(leave_type_final_hd='SL'):
                            availed_hd_sl=availed_hd_sl+1.0

                    else:
                        l_type=availed_FD[0]['leave_type_final_hd']
                        if l_type == 'AL':
                            availed_hd_al=availed_hd_al+1.0
                        elif l_type == 'AB':
                            availed_hd_ab=availed_hd_ab+1.0
                        elif l_type == 'CL':
                            availed_hd_cl=availed_hd_cl+1.0
                        elif l_type == 'SL':
                            availed_hd_sl=availed_hd_sl+1.0
                        elif l_type == 'EL':
                            availed_hd_el=availed_hd_el+1.0

    elif module == 'TDMS':
        attendence_daily_data = PmsAttandanceDeviation.objects.filter(((
            Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
            (Q(leave_type_changed_period__isnull=True)&(Q(deviation_type='FD')|Q(deviation_type='HD')))),
            from_time__date__gte=month_master.year_start_date.date(),
            attandance__employee=user.cu_user.id,is_requested=True).values('from_time__date').distinct()
        
        date_list = [x['from_time__date'] for x in attendence_daily_data.iterator()]
        
        availed_master_wo_reject_fd = PmsAttandanceDeviation.objects.\
            filter((Q(approved_status=1)|Q(approved_status=2)|Q(approved_status=3)),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attandance__employee=user.cu_user.id,
                    attandance__date__date__in=date_list,is_requested=True).annotate(
                        leave_type_final = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='FD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    leave_type_final_hd = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='HD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    ).values('leave_type_final','leave_type_final_hd','attandance__date__date').distinct()
        if availed_master_wo_reject_fd:
            for data in date_list:
                availed_FD=availed_master_wo_reject_fd.filter(attandance__date__date=data)
                #print('availed_FD',availed_FD)
                if availed_FD.filter(leave_type_final__isnull=False):
                    if availed_FD.values('leave_type_final').count() >1:
                        if availed_FD.filter(leave_type_final='AB'):
                            availed_ab=availed_ab+1.0
                        elif availed_FD.filter(leave_type_final='AL'):
                            availed_al = availed_al + 1.0
                        elif availed_FD.filter(leave_type_final='EL'):
                            availed_el = availed_el + 1.0
                        elif availed_FD.filter(leave_type_final='SL'):
                            availed_sl = availed_sl + 1.0
                        elif availed_FD.filter(leave_type_final='CL'):
                            availed_cl = availed_cl + 1.0    
                    else:
                        l_type=availed_FD[0]['leave_type_final']
                        if l_type == 'AL':
                            availed_al = availed_al + 1.0
                        elif l_type == 'AB':
                            availed_ab=availed_ab+1.0
                        elif l_type == 'EL':
                            availed_el=availed_el+1.0
                        elif l_type == 'SL':
                            availed_sl=availed_sl+1.0
                        elif l_type == 'CL':
                            availed_cl=availed_cl+1.0

                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    #print('saddsadsdasdasdasdsadsadsdasdasdad')
                    #print('leave_type_final_hd', availed_FD.values('leave_type_final_hd').count())
                    #time.sleep(10)
                    if availed_FD.values('leave_type_final_hd').count() >1:
                        if availed_FD.filter(leave_type_final_hd='AB'):
                            availed_hd_ab=availed_hd_ab+1.0
                        elif availed_FD.filter(leave_type_final_hd='AL'):
                            availed_hd_al=availed_hd_al+1.0
                        elif availed_FD.filter(leave_type_final_hd='CL'):
                            availed_hd_cl=availed_hd_cl+1.0
                        elif availed_FD.filter(leave_type_final_hd='EL'):
                            availed_hd_el=availed_hd_el+1.0
                        elif availed_FD.filter(leave_type_final_hd='SL'):
                            availed_hd_sl=availed_hd_sl+1.0

                    else:
                        l_type=availed_FD[0]['leave_type_final_hd']
                        if l_type == 'AL':
                            availed_hd_al=availed_hd_al+1.0
                        elif l_type == 'AB':
                            availed_hd_ab=availed_hd_ab+1.0
                        elif l_type == 'CL':
                            availed_hd_cl=availed_hd_cl+1.0
                        elif l_type == 'SL':
                            availed_hd_sl=availed_hd_sl+1.0
                        elif l_type == 'EL':
                            availed_hd_el=availed_hd_el+1.0

    else:
        attendence_daily_data = AttendanceApprovalRequest.objects.filter(((
                Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
                duration_start__date__gte=month_master.year_start_date.date(),
                attendance__employee=user.cu_user.id,is_requested=True).values('duration_start__date').distinct()
        #print("attendence_daily_data",attendence_daily_data)
        date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
        #print("date_list",date_list)
        
        availed_master_wo_reject_fd = AttendanceApprovalRequest.objects.\
            filter((Q(approved_status='pending')|Q(approved_status='approved')|Q(approved_status='reject')),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attendance__employee=user.cu_user.id,
                    attendance_date__in=date_list,is_requested=True,is_deleted=False).annotate(
                        leave_type_final = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(request_type='FD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    leave_type_final_hd = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(request_type='HD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    ).values('leave_type_final','leave_type_final_hd','attendance_date').distinct()
        #print('availed_master_wo_reject_fd',availed_master_wo_reject_fd)
        if availed_master_wo_reject_fd:
            for data in date_list:
                availed_FD=availed_master_wo_reject_fd.filter(attendance_date=data)
                #print("availed_HD",availed_FD)
                if availed_FD.filter(leave_type_final__isnull=False):
                    if availed_FD.values('leave_type_final').count() >1:
                        if availed_FD.filter(leave_type_final='AB'):
                            availed_ab=availed_ab+1.0
                        elif availed_FD.filter(leave_type_final='AL'):
                            availed_al = availed_al + 1.0
                        elif availed_FD.filter(leave_type_final='EL'):
                            availed_el = availed_el + 1.0
                        elif availed_FD.filter(leave_type_final='SL'):
                            availed_sl = availed_sl + 1.0
                        elif availed_FD.filter(leave_type_final='CL'):
                            availed_cl = availed_cl + 1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final']
                        if l_type == 'AL':
                            availed_al = availed_al + 1.0
                        elif l_type == 'AB':
                            availed_ab=availed_ab+1.0
                        elif l_type == 'EL':
                            availed_el=availed_el+1.0
                        elif l_type == 'SL':
                            availed_sl=availed_sl+1.0
                        elif l_type == 'CL':
                            availed_cl=availed_cl+1.0

                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    if availed_FD.values('leave_type_final_hd').count() >1:
                        if availed_FD.filter(leave_type_final_hd='AB'):
                            availed_hd_ab=availed_hd_ab+1.0
                        elif availed_FD.filter(leave_type_final_hd='AL'):
                            availed_hd_al=availed_hd_al+1.0
                        elif availed_FD.filter(leave_type_final_hd='CL'):
                            availed_hd_cl=availed_hd_cl+1.0
                        elif availed_FD.filter(leave_type_final_hd='EL'):
                            availed_hd_el=availed_hd_el+1.0
                        elif availed_FD.filter(leave_type_final_hd='SL'):
                            availed_hd_sl=availed_hd_sl+1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final_hd']
                        if l_type == 'AL':
                            availed_hd_al=availed_hd_al+1.0
                        elif l_type == 'AB':
                            availed_hd_ab=availed_hd_ab+1.0
                        elif l_type == 'CL':
                            availed_hd_cl=availed_hd_cl+1.0
                        elif l_type == 'SL':
                            availed_hd_sl=availed_hd_sl+1.0
                        elif l_type == 'EL':
                            availed_hd_el=availed_hd_el+1.0

    return availed_al,availed_ab,availed_cl,availed_el,availed_sl,availed_hd_al,availed_hd_ab,availed_hd_cl,availed_hd_el,availed_hd_sl

def get_advanceLeaveDetails(month_master,date_object=None,user=None,module='HRMS'):
    if module == 'PMS':
        last_attendance = PmsAttendance.objects.filter(employee=user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
        last_attendance = last_attendance[0] if last_attendance else date_object
    
    elif module == 'TDMS':
        last_attendance = PmsAttendance.objects.filter(employee=user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
        last_attendance = last_attendance[0] if last_attendance else date_object
    
    else:
        last_attendance = Attendance.objects.filter(employee=user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
        last_attendance = last_attendance[0] if last_attendance else date_object

    #print('last_attendance',last_attendance)
    advance_leave = EmployeeAdvanceLeaves.objects.filter(
                    (Q(approved_status = 'pending') | Q(approved_status = 'approved')),
                     employee=user.cu_user,
                     is_deleted=False,
                     start_date__date__gt = last_attendance,
                     end_date__date__gt = last_attendance,
                     
                    ).values('leave_type','start_date','end_date')
    # advance_leave=EmployeeAdvanceLeaves.objects.filter(
    #         Q(employee=user.cu_user)
    #         &Q(is_deleted=False)
    #         &(
    #             Q(approved_status='pending')|Q(approved_status='approved')
    #             )
    #         &Q(start_date__date__lte=month_master.month_end.date())
    #         ).values('leave_type','start_date','end_date')
    #print('advance_leave',advance_leave)
    advance_al=0
    advance_ab=0
    advance_el=0
    advance_cl=0
    day=0

    
    
    if last_attendance<month_master.month_end.date():
        #print("last_attendancehfthtfrhfth",last_attendance)
        adv_str_date = last_attendance+timedelta(days=1)
        adv_end_date = month_master.year_end_date.date()+timedelta(days=1)
        #print('adv_str_date,adv_end_date',adv_str_date,adv_end_date)

        if advance_leave:
            for leave in advance_leave:
                #print('leave',leave)
                start_date=leave['start_date'].date()
                end_date=leave['end_date'].date()+timedelta(days=1)
                #print('start_date,end_date',start_date,end_date)

                if adv_str_date<=start_date and adv_end_date>=start_date:
                    if adv_end_date>=end_date:
                        day = (end_date-start_date).days
                    elif adv_end_date<=end_date:
                        day = (adv_end_date-start_date).days
                elif adv_str_date>start_date:
                    if adv_end_date<=end_date:
                        day = (adv_end_date-adv_str_date).days
                    elif adv_str_date<=end_date and adv_end_date>=end_date:
                        day = (end_date-adv_str_date).days

                if leave['leave_type']=='AL':
                    advance_al+=day
                    #print('advance_al',advance_al)
                elif leave['leave_type']=='AB':
                    advance_ab+=day
                elif leave['leave_type']=='CL':
                    advance_cl+=day
                elif leave['leave_type']=='EL':
                    advance_el+=day

    return advance_al,advance_ab,advance_el,advance_cl

def get_monthlyODdetails(month_master,date_object=None,user=None):

        monthly_availed_data = AttendanceApprovalRequest.objects.filter(attendance__employee=user.cu_user,
                                                                    is_requested=True, is_deleted=False,
                                                                    duration_start__gte=month_master.month_start,
                                                                    duration_start__lte=month_master.month_end)

        monthly_od_count = monthly_availed_data.filter(Q(is_requested=True) & Q(is_deleted=False) &
                                                    (Q(request_type='FOD') | Q(request_type='POD')) &
                                                    (Q(approved_status='pending') | Q(approved_status='approved')
                                                        )).count()

        monthly_od_duration = monthly_availed_data.filter(Q(is_requested=True) & Q(is_deleted=False) &
                                                        (Q(request_type='FOD') | Q(request_type='POD')) &
                                                        (Q(approved_status='pending') | Q(approved_status='approved')
                                                        )).aggregate(Sum('duration'))['duration__sum']

        monthly_od_duration = monthly_od_duration if monthly_od_duration else 0

        return monthly_od_duration,monthly_od_count

def get_pmsAttandanceLeaveBalanceTransferLog(month_master,date_object:None,employee:None):
        pmsAttandanceLeaveBalanceTransferLog = PmsAttandanceLeaveBalanceTransferLog.objects.filter(
            attendance_date__gte=month_master.year_start_date.date(),
            attendance_date__lte=date_object,
            attendance__employee=employee,
            is_deleted=False
            )
        
        print('pmsAttandanceLeaveBalanceTransferLog',pmsAttandanceLeaveBalanceTransferLog)
        #print('fortnightLeaveDeductionLogdetails',fortnightLeaveDeductionLogdetails.query)
        
        cl_deduction = 0.0
        el_deduction = 0.0
        sl_deduction = 0.0
        al_deduction = 0.0
        ab_deduction = 0.0

        for  each in pmsAttandanceLeaveBalanceTransferLog:
            
                if each.deviation_type == 'HD':
                    
                    if each.leave_type == 'AL':
                        al_deduction += 0.5
                    if each.leave_type == 'AB':
                        ab_deduction += 0.5
                    if each.leave_type == 'CL':
                        cl_deduction += 0.5
                    if each.leave_type == 'EL':
                        el_deduction += 0.5
                    if each.leave_type == 'SL':
                        sl_deduction += 0.5
                    
                if each.deviation_type == 'FD':
                    if each.leave_type == 'AL':
                        al_deduction += 1.0
                    if each.leave_type == 'AB':
                        ab_deduction += 1.0
                    if each.leave_type == 'CL':
                        cl_deduction += 1.0
                    if each.leave_type == 'EL':
                        el_deduction += 1.0
                    if each.leave_type == 'SL':
                        sl_deduction += 1.0

        print(al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction)
        return al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction

def get_fortnight_leave_deduction_count(month_master,date_object:None,employee:None):
        fortnightLeaveDeductionLogdetails = PmsAttandanceFortnightLeaveDeductionLog.objects.filter(
            attendance__date__date__gte=month_master.year_start_date.date(),
            attendance__date__date__lte=date_object,
            attendance__employee=employee,
            is_deleted=False
            )
        
        print('fortnightLeaveDeductionLogdetails',fortnightLeaveDeductionLogdetails)
        #print('fortnightLeaveDeductionLogdetails',fortnightLeaveDeductionLogdetails.query)
        
        cl_deduction = 0.0
        el_deduction = 0.0
        sl_deduction = 0.0
        al_deduction = 0.0
        ab_deduction = 0.0

        for  e_fortnightLeaveDeductionLogdetails in fortnightLeaveDeductionLogdetails:
            
                if e_fortnightLeaveDeductionLogdetails.deviation_type == 'HD':
                    
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'AL':
                        al_deduction += 0.5
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'AB':
                        ab_deduction += 0.5
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'CL':
                        cl_deduction += 0.5
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'EL':
                        el_deduction += 0.5
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'SL':
                        sl_deduction += 0.5
                    
                if e_fortnightLeaveDeductionLogdetails.deviation_type == 'FD':
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'AL':
                        al_deduction += 1.0
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'AB':
                        ab_deduction += 1.0
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'CL':
                        cl_deduction += 1.0
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'EL':
                        el_deduction += 1.0
                    if e_fortnightLeaveDeductionLogdetails.leave_type == 'SL':
                        sl_deduction += 1.0

        print(al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction)
        return al_deduction,ab_deduction,cl_deduction,el_deduction,sl_deduction

'''
    End Leave Calculation [If you want to edit then please check first then edit]
'''

def advance_leave_calculation_excluding_current_month(tcore_user=None, date_object=None):
    from datetime import timedelta,date
    
    month_master=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                month_end__date__gte=date_object,is_deleted=False).first()
    
    # ::````Advance Leave Calculation```:: #
    
    advance_leave = EmployeeAdvanceLeaves.objects.filter(Q(employee=tcore_user.cu_user)&
                                                        Q(is_deleted=False)&
                                                        (Q(approved_status='pending')|Q(approved_status='approved'))
                                                        ).order_by('-start_date')
    #print('advance_leave',advance_leave)     
    advance_al=0.0
    advance_ab=0.0
    advance_cl=0.0
    advance_el=0.0
    day=0


    # last_attendance = Attendance.objects.filter(employee=tcore_user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
    # print("last_attendance",last_attendance)
    # last_attendance = last_attendance[0] if last_attendance else date_object

    last_advance_leave_date = advance_leave.first().end_date if advance_leave.first() else month_master.month_end

    adv_str_date = month_master.month_end.date()+timedelta(days=1)
    adv_end_date = last_advance_leave_date.date()+timedelta(days=1)

    
    '''
        Get total leave allocation(monthly) by request start and end date
    '''
    leave_allocation_per_month = 0.0
    leave_allocation_per_month_cl = 0.0
    leave_allocation_per_month_sl = 0.0
    leave_allocation_per_month_el = 0.0

    leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
            (
                Q(month__month_start__date__gte=month_master.year_start_date.date(),month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,month__month_end__date__gte=date_object)
            ),employee=tcore_user.cu_user)

    if tcore_user.salary_type and leave_allocation_per_month_d:

        if tcore_user.salary_type.st_code == 'FF' or tcore_user.salary_type.st_code == 'EE':
            leave_allocation_per_month = leave_allocation_per_month_d.aggregate(Sum('round_figure'))['round_figure__sum']

        if tcore_user.salary_type.st_code == 'CC' or tcore_user.salary_type.st_code == 'DD':
            #print('round_cl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum'])
            #print('round_el_allotted',leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum'])
            #print('round_sl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum'])
            leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
            leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
            leave_allocation_per_month_sl = leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum']

        
        if tcore_user.salary_type.st_code == 'BB':
            leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
            leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']

        if tcore_user.salary_type.st_code == 'AA':
            leave_allocation_per_month_cl = 0.0
            leave_allocation_per_month_el = 0.0
            leave_allocation_per_month_sl = 0.0
            leave_allocation_per_month = 0.0


    #print('leave_allocation_per_month',leave_allocation_per_month)  
    #logger.info(leave_allocation_per_month)      


    if adv_str_date < adv_end_date:
        if advance_leave:
            for leave in advance_leave:
                #print('leave',leave)
                start_date=leave.start_date.date()
                end_date=leave.end_date.date()+timedelta(days=1)
                #print('start_date,end_date',start_date,end_date)

                if adv_str_date<=start_date and adv_end_date>=start_date:
                    if adv_end_date>=end_date:
                        day = (end_date-start_date).days
                    elif adv_end_date<=end_date:
                        day = (adv_end_date-start_date).days
                elif adv_str_date>start_date:
                    if adv_end_date<=end_date:
                        day = (adv_end_date-adv_str_date).days
                    elif adv_str_date<=end_date and adv_end_date>=end_date:
                        day = (end_date-adv_str_date).days

                if leave.leave_type=='AL':
                    advance_al+=day
                elif leave.leave_type=='AB':
                    advance_ab+=day
                elif leave.leave_type == 'CL':
                    advance_cl += day
                elif leave.leave_type == 'EL':
                    advance_el += day
    
    is_advance_leave_taken = advance_al > 0
    is_advance_leave_taken_cl = advance_cl > 0
    is_advance_leave_taken_el = advance_el > 0

    #logger.info(advance_al)

    advance_leave_balance = float(leave_allocation_per_month) - advance_al
    advance_leave_balance_el = float(leave_allocation_per_month_el) - advance_el
    advance_leave_balance_cl = float(leave_allocation_per_month_cl) - advance_cl

    is_leave_taken_from_current_month = advance_leave_balance < 0
    is_leave_taken_from_current_month_cl = advance_leave_balance_cl < 0
    is_leave_taken_from_current_month_el = advance_leave_balance_el < 0

    result = {
        'is_advance_leave_taken': is_advance_leave_taken,
        'is_advance_leave_taken_cl': is_advance_leave_taken_cl,
        'is_advance_leave_taken_el': is_advance_leave_taken_el,
        'is_leave_taken_from_current_month': is_leave_taken_from_current_month,
        'is_leave_taken_from_current_month_cl': is_leave_taken_from_current_month_cl,
        'is_leave_taken_from_current_month_el': is_leave_taken_from_current_month_el,
        'advance_al': advance_al,
        'advance_el': advance_el,
        'advance_cl': advance_cl,
        'advance_ab': advance_ab,
        'leave_allocation': float(leave_allocation_per_month),
        'advance_leave_balance': advance_leave_balance,
        'advance_leave_balance_el':advance_leave_balance_el,
        'advance_leave_balance_cl':advance_leave_balance_cl
    }

    return result





def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier


def late_login_or_early_logout_count_excluding_benchmark(instance=None, user=None):
    # instance.duration_end == instance.attendance.login_time or instance.duration_start == instance.attendance.logout_time
    month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=instance.attendance_date,
                                                        month_end__date__gte=instance.attendance_date).first()
    bench_15m_request = AttendanceApprovalRequest.objects.filter(
        Q(attendance__employee=user) &
        Q(is_requested=True) &
        Q(checkin_benchmark=False) &
        Q(request_type='GR') &
        Q(duration_start__date__gte=month_master.month_start.date()) &
        Q(duration_start__date__lt=instance.attendance_date) &
        Q(is_deleted=False))
    print('bench_15m_request:', bench_15m_request)
    print('bench_15m_request count:', bench_15m_request.count())

    attendance_set = set()
    for attendance_request in bench_15m_request:
        attendance_set.add(attendance_request.attendance)
    print('attendance_set:', attendance_set)
    login_logout_requests = AttendanceApprovalRequest.objects.none()
    for attendance in attendance_set:
        login_logout_requests = login_logout_requests | bench_15m_request.filter(Q(attendance=attendance) &
                                                                                 Q(
                                                                                     Q(
                                                                                         duration_end=attendance.login_time) |
                                                                                     Q(
                                                                                         duration_start=attendance.logout_time)
                                                                                 )
                                                                                 )
    print('login_logout_requests:', login_logout_requests)

    return login_logout_requests.values('attendance').distinct().count()


def late_login_count_excluding_benchmark(instance=None, user=None):
    # instance.duration_end == instance.attendance.login_time or instance.duration_start == instance.attendance.logout_time
    month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=instance.attendance_date,
                                                        month_end__date__gte=instance.attendance_date).first()
    grace_requests = AttendanceApprovalRequest.objects.filter(
        Q(attendance__employee=user) &
        Q(is_requested=True) &
        Q(checkin_benchmark=False) &
        Q(request_type='GR') &
        Q(duration_start__date__gte=month_master.month_start.date()) &
        Q(duration_start__date__lt=instance.attendance_date) &
        Q(is_deleted=False))
    print('grace_requests:', grace_requests)
    print('grace_requests count:', grace_requests.count())

    attendance_set = {attendance_request.attendance for attendance_request in grace_requests}
    print('attendance_set:', attendance_set)
    login_requests = AttendanceApprovalRequest.objects.none()
    for attendance in attendance_set:
        login_requests = login_requests | grace_requests.filter(
            Q(attendance=attendance) & Q(duration_end=attendance.login_time))
    print('login_requests:', login_requests)

    return login_requests.values('attendance').distinct().count()


def early_logout_count_excluding_benchmark(instance=None, user=None):
    # instance.duration_end == instance.attendance.login_time or instance.duration_start == instance.attendance.logout_time
    month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=instance.attendance_date,
                                                        month_end__date__gte=instance.attendance_date).first()
    grace_requests = AttendanceApprovalRequest.objects.filter(
        Q(attendance__employee=user) &
        Q(is_requested=True) &
        Q(checkin_benchmark=False) &
        Q(request_type='GR') &
        Q(duration_start__date__gte=month_master.month_start.date()) &
        Q(duration_start__date__lt=instance.attendance_date) &
        Q(is_deleted=False))
    print('grace_requests:', grace_requests)
    print('grace_requests count:', grace_requests.count())

    attendance_set = {attendance_request.attendance for attendance_request in grace_requests}
    print('attendance_set:', attendance_set)
    logout_requests = AttendanceApprovalRequest.objects.none()
    for attendance in attendance_set:
        logout_requests = logout_requests | grace_requests.filter(
            Q(attendance=attendance) & Q(duration_start=attendance.logout_time))
    print('logout_requests:', logout_requests)

    return logout_requests.values('attendance').distinct().count()


def get_documents(request=None, attendance_request=None):
    doc_list = []
    documents = AttandanceApprovalDocuments.objects.filter(request=attendance_request, is_deleted=False)
    for document in documents:
        doc_dict = {
            'id': document.id,
            'document_name': document.document_name,
            'user_id': document.created_by.id,
            "user_name": document.created_by.username,
            'document': request.build_absolute_uri(document.document.url)
        }
        doc_list.append(doc_dict)
    return doc_list


def calculate_day_remarks(user=None, date_obj=None, which_module=None):
    remarks = None

    if which_module == 'PMS':
        availed_FD = PmsAttandanceDeviation.objects. \
            filter((Q(approved_status=1) | Q(approved_status=2) | Q(approved_status=3)),
                   (Q(leave_type__isnull=False) | Q(leave_type_changed_period__isnull=False)),
                   attandance__employee_id=user,
                   attandance__date__date=date_obj, is_requested=True).annotate(
            leave_type_final=Case(
                When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='FD')),
                     then=F('leave_type_changed')),
                When((Q(leave_type_changed_period__isnull=True) & Q(deviation_type='FD')), then=F('leave_type')),
                output_field=CharField()
            ),
            leave_type_final_hd=Case(
                When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='HD')),
                     then=F('leave_type_changed')),
                When((Q(leave_type_changed_period__isnull=True) & Q(deviation_type='HD')), then=F('leave_type')),
                output_field=CharField()
            ),
        ).values('leave_type_final', 'leave_type_final_hd', 'attandance__date__date').distinct()

        # print("availed_HD",availed_FD)
        if availed_FD.filter(leave_type_final__isnull=False):
            if availed_FD.values('leave_type_final').count() > 1:
                if availed_FD.filter(leave_type_final='AB'):
                    remarks = 'Leave(AB)'
                elif availed_FD.filter(leave_type_final='AL'):
                    remarks = 'Leave(AL)'
            else:
                l_type = availed_FD[0]['leave_type_final']
                if l_type == 'AL':
                    remarks = 'Leave(AL)'
                elif l_type == 'AB':
                    remarks = 'Leave(AB)'

        elif availed_FD.filter(leave_type_final_hd__isnull=False):
            if availed_FD.values('leave_type_final_hd').count() > 1:
                if availed_FD.filter(leave_type_final_hd='AB'):
                    remarks = 'Leave(AB)'
                elif availed_FD.filter(leave_type_final_hd='AL'):
                    remarks = 'Leave(AL)'
            else:
                l_type = availed_FD[0]['leave_type_final_hd']
                if l_type == 'AL':
                    remarks = 'Leave(AL)'
                elif l_type == 'AB':
                    remarks = 'Leave(AB)'

        print('PMS', remarks)


    else:

        availed_FD = AttendanceApprovalRequest.objects. \
            filter((Q(approved_status='pending') | Q(approved_status='approved') | Q(approved_status='reject')),
                   (Q(leave_type__isnull=False) | Q(leave_type_changed_period__isnull=False)),
                   attendance__employee=user,
                   attendance_date=date_obj, is_requested=True, is_deleted=False).annotate(
            leave_type_final=Case(
                When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='FD')),
                     then=F('leave_type_changed')),
                When((Q(leave_type_changed_period__isnull=True) & Q(request_type='FD')), then=F('leave_type')),
                output_field=CharField()
            ),
            leave_type_final_hd=Case(
                When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='HD')),
                     then=F('leave_type_changed')),
                When((Q(leave_type_changed_period__isnull=True) & Q(request_type='HD')), then=F('leave_type')),
                output_field=CharField()
            ),
        ).values('leave_type_final', 'leave_type_final_hd', 'attendance_date').distinct()

        # print("availed_HD",availed_FD)
        if availed_FD.filter(leave_type_final__isnull=False):
            if availed_FD.values('leave_type_final').count() > 1:
                if availed_FD.filter(leave_type_final='AB'):
                    remarks = 'Leave(AB)'
                elif availed_FD.filter(leave_type_final='AL'):
                    remarks = 'Leave(AL)'
                elif availed_FD.filter(leave_type_final='CL'):
                    remarks = 'Leave(CL)'
                elif availed_FD.filter(leave_type_final='EL'):
                    remarks = 'Leave(EL)'
                elif availed_FD.filter(leave_type_final='SL'):
                    remarks = 'Leave(SL)'
            else:
                l_type = availed_FD[0]['leave_type_final']
                if l_type == 'AL':
                    remarks = 'Leave(AL)'
                elif l_type == 'AB':
                    remarks = 'Leave(AB)'
                elif l_type == 'CL':
                    remarks = 'Leave(CL)'
                elif l_type == 'SL':
                    remarks = 'Leave(SL)'
                elif l_type == 'EL':
                    remarks = 'Leave(EL)'

        elif availed_FD.filter(leave_type_final_hd__isnull=False):
            if availed_FD.values('leave_type_final_hd').count() > 1:
                if availed_FD.filter(leave_type_final_hd='AB'):
                    remarks = 'Leave(AB)'
                elif availed_FD.filter(leave_type_final_hd='AL'):
                    remarks = 'Leave(AL)'
                elif availed_FD.filter(leave_type_final_hd='CL'):
                    remarks = 'Leave(CL)'
                elif availed_FD.filter(leave_type_final_hd='SL'):
                    remarks = 'Leave(SL)'
                elif availed_FD.filter(leave_type_final_hd='EL'):
                    remarks = 'Leave(EL)'
            else:
                l_type = availed_FD[0]['leave_type_final_hd']
                if l_type == 'AL':
                    remarks = 'Leave(AL)'
                elif l_type == 'AB':
                    remarks = 'Leave(AB)'
                elif l_type == 'CL':
                    remarks = 'Leave(CL)'
                elif l_type == 'EL':
                    remarks = 'Leave(EL)'
                elif l_type == 'SL':
                    remarks = 'Leave(SL)'

    return remarks


def get_month_first_last_datetime(year=None, month=None):
    _, last_date = calendar.monthrange(year, month)
    month_start = '{}-{}-{}'.format(year, month, 1)
    month_end = '{}-{}-{}'.format(year, month, last_date)
    month_start_date = datetime.datetime.strptime(month_start, "%Y-%m-%d").date()
    month_end_date = datetime.datetime.strptime(month_end, "%Y-%m-%d").date()
    return month_start_date, month_end_date


def daterange(start_date, end_date):
    from datetime import timedelta, date
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + timedelta(n)


#:::::: FLEXI :::::::#
def get_flexi_working_hour_and_login_logout_time(tcore_user=None, date_obj=None):
    attendance = Attendance.objects.filter(employee=tcore_user.cu_user, date__date=date_obj).first()
    # print('date,attendance',date_obj,attendance)
    attendance_requests = AttendanceApprovalRequest.objects.filter(attendance=attendance, is_deleted=False).order_by(
        'duration_start')
    work_hour = 0.0
    break_hour = 0.0
    if attendance:
        if attendance.is_present:
            break_hour_requests = attendance_requests.filter((Q(approved_status='relese') |
                                                              Q(approved_status='reject') |
                                                              Q(approved_status='regular') |
                                                              Q(request_type='HD') |
                                                              Q(request_type='FD')) &
                                                             (Q(duration_start__gte=attendance.login_time) &
                                                              Q(duration_start__lte=attendance.logout_time))).aggregate(
                Sum('duration'))
            break_hour = float(break_hour_requests['duration__sum']) if break_hour_requests['duration__sum'] else 0.0
            deviation_requests = attendance_requests.filter((Q(approved_status='pending') |
                                                             Q(approved_status='approved')) &
                                                            (Q(request_type='OD') |
                                                             Q(request_type='WFH')) &
                                                            (Q(duration_start__lte=attendance.login_time) &
                                                             Q(duration_start__gte=attendance.logout_time))).aggregate(
                Sum('duration'))
            total_deviation_duration = float(deviation_requests['duration__sum']) if deviation_requests[
                'duration__sum'] else 0.0
            login_logout_duration = (attendance.logout_time - attendance.login_time).seconds / 60
            work_hour = total_deviation_duration + login_logout_duration - break_hour
            # print('total_deviation_duration', total_deviation_duration)
            # print('login_logout_duration', login_logout_duration)
            # print('break_hour',break_hour)
            # print('work_hour',work_hour)
        else:
            deviation_requests = attendance_requests.filter((Q(approved_status='pending') |
                                                             Q(approved_status='approved')) &
                                                            (Q(request_type='OD') |
                                                             Q(request_type='WFH'))).aggregate(
                Sum('duration'))
            total_deviation_duration = float(deviation_requests['duration__sum']) if deviation_requests[
                'duration__sum'] else 0.0
            work_hour = total_deviation_duration
            # print('work_hour',work_hour)

    return work_hour


#:::::: FLEXI :::::::#
def is_flexi_date_active(tcore_user=None, date_ob=None):
    active_day = True
    is_hd_al_ab = False

    state_obj = tcore_user.job_location_state
    default_state = TCoreState.objects.filter(cs_state_name__iexact='west bengal').first()
    t_core_state_id = state_obj.id if state_obj else default_state.id
    holiday = HolidayStateMapping.objects.filter(
        Q(holiday__holiday_date=date_ob) & Q(state__id=t_core_state_id)).values('holiday__holiday_name')

    special_full_day = AttendanceSpecialdayMaster.objects.filter(full_day__date=date_ob, is_deleted=False).values(
        'full_day__date', 'remarks')

    # Holiday, Full Spacial Day, Calculation #
    if holiday or special_full_day or date_ob.weekday() == 6:
        active_day = False
        # print('holiday or special_full_day or date_ob.weekday()==6')

    # Off-Saturday calculation #
    if date_ob.weekday() == 5:
        ## logic??? difference between AttendenceSaturdayOffMaster? meaning of all_s_day?
        '''
            filtering the AttendenceSaturdayOffMaster to get the off saturday.
            all_s_day :: All Saturday off
        '''
        saturday_off_list = AttendenceSaturdayOffMaster.objects.filter(employee=tcore_user.cu_user,
                                                                       is_deleted=False).values(
            'first', 'second', 'third', 'fourth', 'all_s_day').order_by('-id')

        # print("saturday_off_list",date_ob.weekday(), saturday_off_list)

        if saturday_off_list:
            if saturday_off_list[0]['all_s_day'] is True:
                active_day = False
                # print("saturday_off_list[0]['all_s_day'] is True")
            else:
                week_date = date_ob.day
                # print("week_date",  week_date)
                month_calender = calendar.monthcalendar(date_ob.year, date_ob.month)
                saturday_list = (0, 1, 2, 3) if month_calender[0][calendar.SATURDAY] else (1, 2, 3, 4)

                if saturday_off_list[0]['first'] is True and int(week_date) == int(
                        month_calender[saturday_list[0]][calendar.SATURDAY]):
                    active_day = False
                    # print("saturday_off_list[0]['first'] is True and int(week_date)==int(month_calender[saturday_list[0]][calendar.SATURDAY])")
                elif saturday_off_list[0]['second'] is True and int(week_date) == int(
                        month_calender[saturday_list[1]][calendar.SATURDAY]):
                    active_day = False
                    # print("saturday_off_list[0]['second'] is True and int(week_date)==int(month_calender[saturday_list[1]][calendar.SATURDAY])")
                elif saturday_off_list[0]['third'] is True and int(week_date) == int(
                        month_calender[saturday_list[2]][calendar.SATURDAY]):
                    active_day = False
                    # print("saturday_off_list[0]['third'] is True and int(week_date)==int(month_calender[saturday_list[2]][calendar.SATURDAY])")
                elif saturday_off_list[0]['fourth'] is True and int(week_date) == int(
                        month_calender[saturday_list[3]][calendar.SATURDAY]):
                    active_day = False
                    # print("saturday_off_list[0]['fourth'] is True and int(week_date)==int(month_calender[saturday_list[3]][calendar.SATURDAY])")

    last_attendance = Attendance.objects.filter(employee=tcore_user.cu_user).order_by('-date').first()

    if last_attendance:
        if last_attendance.date.date() < date_ob:
            advance_leave = EmployeeAdvanceLeaves.objects.filter(
                Q(start_date__date__lte=date_ob) & Q(end_date__date__gte=date_ob) & Q(employee=tcore_user.cu_user) &
                (Q(approved_status='pending') | Q(approved_status='approved'))).values('leave_type', 'reason')

            spacial_leave = EmployeeSpecialLeaves.objects.filter(
                Q(start_date__date__lte=date_ob) & Q(end_date__date__gte=date_ob) & Q(employee=tcore_user.cu_user) &
                (Q(approved_status='pending') | Q(approved_status='approved'))).values('leave_type', 'reason')
            # Spacial leave, Advance leave
            if spacial_leave:
                active_day = False
                # print("spacial_leave")
            elif advance_leave:
                active_day = False
                # print("advance_leave")
        else:
            availed_FD = AttendanceApprovalRequest.objects. \
                filter((Q(approved_status='pending') | Q(approved_status='approved') | Q(approved_status='reject')),
                       (Q(leave_type__isnull=False) | Q(leave_type_changed_period__isnull=False)),
                       attendance__employee=tcore_user.cu_user,
                       attendance_date=date_ob, is_requested=True, is_deleted=False).annotate(
                leave_type_final=Case(
                    When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='FD')),
                         then=F('leave_type_changed')),
                    When((Q(leave_type_changed_period__isnull=True) & Q(request_type='FD')), then=F('leave_type')),
                    output_field=CharField()
                ),
                leave_type_final_hd=Case(
                    When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='HD')),
                         then=F('leave_type_changed')),
                    When((Q(leave_type_changed_period__isnull=True) & Q(request_type='HD')), then=F('leave_type')),
                    output_field=CharField()
                ),
            ).values('leave_type_final', 'leave_type_final_hd', 'attendance_date').distinct()

            # When request_type = FD and any leave_type exist
            if availed_FD.filter(leave_type_final__isnull=False):
                active_day = False
            elif availed_FD.filter(leave_type_final_hd__isnull=False):
                is_hd_al_ab = True

    return active_day, is_hd_al_ab


#:::::: FLEXI :::::::#
def get_flexi_hours_for_work_days(tcore_user=None, start_date=None, end_date=None):
    total_hours = 0.0
    working_hours = 0.0

    for date_ob in daterange(start_date.date(), end_date.date()):

        active_day, is_hd_al_ab = is_flexi_date_active(tcore_user=tcore_user, date_ob=date_ob)

        # print('date', date_ob, ' status', active_day)
        if active_day:
            per_day_working_hour = (90 / 11) * 60 - 4 * 60 if is_hd_al_ab else (90 / 11) * 60
            total_hours += per_day_working_hour
            working_hours += get_flexi_working_hour_and_login_logout_time(tcore_user=tcore_user, date_obj=date_ob)

    return total_hours, working_hours


def get_fortnight_leave_deduction(hour=None):
    quotient, reminder = divmod(hour, 4)
    leave_deduction = 0
    if reminder > 0:
        leave_deduction = (quotient + 1) * 0.5
    else:
        leave_deduction = quotient * 0.5

    return leave_deduction


def get_leave_type_from_type(date):
    # print('date',date)
    queryset_leave_check = EmployeeAdvanceLeaves.objects.filter(
        start_date__date__lte=date,
        end_date__date__gte=date, is_deleted=False).values('leave_type', 'approved_status', 'remarks').first()
    # print('queryset_leave_check',queryset_leave_check)
    if not queryset_leave_check:
        queryset_leave_check = EmployeeSpecialLeaves.objects.filter(
            start_date__date__lte=date,
            end_date__date__gte=date, is_deleted=False).values('leave_type', 'approved_status', 'remarks').first()
    return queryset_leave_check


#:::::::::::::: PMS FLEXI :::::::::::::::::#
def is_pms_flexi_date_active(tcore_user=None, date_ob=None):
    active_day = True
    is_hd_al_ab = False

    last_attendance = PmsAttendance.objects.filter(employee=tcore_user.cu_user).order_by('-date').first()

    if last_attendance:
        if last_attendance.date.date() < date_ob:
            advance_leave = EmployeeAdvanceLeaves.objects.filter(
                Q(start_date__date__lte=date_ob) & Q(end_date__date__gte=date_ob) & Q(employee=tcore_user.cu_user) &
                (Q(approved_status=1) | Q(approved_status=2))).values('leave_type', 'reason')

            spacial_leave = EmployeeSpecialLeaves.objects.filter(
                Q(start_date__date__lte=date_ob) & Q(end_date__date__gte=date_ob) & Q(employee=tcore_user.cu_user) &
                (Q(approved_status=1) | Q(approved_status=2))).values('leave_type', 'reason')
            # Spacial leave, Advance leave
            if spacial_leave:
                active_day = False
                # print("spacial_leave")
            elif advance_leave:
                active_day = False
                # print("advance_leave")
        else:
            availed_FD = PmsAttandanceDeviation.objects. \
                filter((Q(approved_status=1) | Q(approved_status=2) | Q(approved_status=3)),
                       (Q(leave_type__isnull=False) | Q(leave_type_changed_period__isnull=False)),
                       attandance__employee=tcore_user.cu_user,
                       attandance__date__date=date_ob, is_requested=True).annotate(
                leave_type_final=Case(
                    When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='FD')),
                         then=F('leave_type_changed')),
                    When((Q(leave_type_changed_period__isnull=True) & Q(deviation_type='FD')), then=F('leave_type')),
                    output_field=CharField()
                ),
                leave_type_final_hd=Case(
                    When((Q(leave_type_changed_period__isnull=False) & Q(leave_type_changed_period='HD')),
                         then=F('leave_type_changed')),
                    When((Q(leave_type_changed_period__isnull=True) & Q(deviation_type='HD')), then=F('leave_type')),
                    output_field=CharField()
                ),
            ).values('leave_type_final', 'leave_type_final_hd', 'attandance__date__date').distinct()
            # print('availed_FD',availed_FD)
            # When request_type = FD and any leave_type exist
            if availed_FD.filter(leave_type_final__isnull=False):
                active_day = False
                # print('active_day')
            elif availed_FD.filter(leave_type_final_hd__isnull=False):
                is_hd_al_ab = True
                # print('is_hd_al_ab')

    return active_day, is_hd_al_ab


#:::::::::::::: PMS FLEXI :::::::::::::::::#
def get_pms_flexi_working_hour_and_login_logout_time(tcore_user=None, date_obj=None, fortnight_flag_cron=False):
    attendance = PmsAttendance.objects.filter(employee=tcore_user.cu_user, date__date=date_obj).first()
    # print('date,attendance',date_obj,attendance)
    attendance_requests = PmsAttandanceDeviation.objects.filter(attandance=attendance).order_by('from_time')
    work_hour = 0.0
    break_hour = 0.0
    if attendance:
        if attendance.is_present:
            # attendance_log = PmsAttandanceLog.objects.filter(attandance=attendance,is_deleted=False)

            queryset_att_log = PmsAttandanceLog.objects.filter(attandance=attendance,
                                                               login_logout_check__in=('Logout',), is_deleted=False)

            if queryset_att_log:
                login_logout_duration = 0.0
                for e_queryset_att_log in queryset_att_log:
                    login_time = PmsAttandanceLog.objects.filter(attandance=attendance,
                                                                 id=e_queryset_att_log.login_id).values_list('time',
                                                                                                             flat=True).first()
                    logout_time = e_queryset_att_log.time
                    # login_time = attendance_log.filter(login_logout_check='Login').order_by('time').first().time if attendance_log.filter(login_logout_check='Login').count() else None
                    # logout_time = attendance_log.filter(login_logout_check='Logout').order_by('time').first().time if attendance_log.filter(login_logout_check='Logout').count() else None
                    # print('login',login_time,'logout', logout_time)

                    if login_time and logout_time:
                        login_logout_duration += (logout_time - login_time).seconds / 60

                # print('login_logout_duration',login_logout_duration)
                if login_logout_duration:
                    if fortnight_flag_cron:
                        break_hour_requests = attendance_requests.filter(
                            (
                                # Q(approved_status=1)|
                                    Q(approved_status=5) |
                                    Q(approved_status=3) |
                                    # Q(approved_status=4)|
                                    Q(deviation_type='HD') |
                                    Q(deviation_type='FD')
                            )
                        ).aggregate(Sum('duration'))

                    else:
                        break_hour_requests = attendance_requests.filter(
                            (
                                    Q(approved_status=1) |
                                    Q(approved_status=5) |
                                    Q(approved_status=3) |
                                    Q(approved_status=4) |
                                    Q(deviation_type='HD') |
                                    Q(deviation_type='FD')
                            )
                        ).aggregate(Sum('duration'))

                    break_hour = float(break_hour_requests['duration__sum']) if break_hour_requests[
                        'duration__sum'] else 0.0
                    work_hour = login_logout_duration - break_hour

                else:
                    deviation_requests = attendance_requests.filter((Q(approved_status=1) |
                                                                     Q(approved_status=2)) &
                                                                    Q(deviation_type='OD')).aggregate(
                        Sum('duration'))
                    total_deviation_duration = float(deviation_requests['duration__sum']) if deviation_requests[
                        'duration__sum'] else 0.0
                    work_hour = total_deviation_duration
            # print('work_hour',work_hour)
    # print('date_obj',date_obj,'work_hour',work_hour)
    # time.sleep(1)
    return work_hour


#:::::::::::::: PMS FLEXI :::::::::::::::::#
def get_pms_flexi_hours_for_work_days(tcore_user=None, start_date=None, end_date=None, fortnight_flag_cron=False):
    # print('tcore_user',tcore_user.cu_user,start_date,end_date)
    total_hours = 0.0
    working_hours = 0.0
    start_date = start_date.date()
    end_date = end_date.date()
    for date_ob in daterange(start_date, end_date):
        # print('date',date_ob, type(date_ob))

        active_day, is_hd_al_ab = is_pms_flexi_date_active(tcore_user=tcore_user, date_ob=date_ob)
        # print("date_ob, active_day, is_hd_al_ab",date_ob, active_day, is_hd_al_ab)
        # print('date', date_ob, ' status', active_day)
        if active_day:
            per_day_working_hour = 8 * 60 - 4 * 60 if is_hd_al_ab else 8 * 60
            total_hours += per_day_working_hour
            working_hours += get_pms_flexi_working_hour_and_login_logout_time(tcore_user=tcore_user, date_obj=date_ob,
                                                                              fortnight_flag_cron=fortnight_flag_cron)

    # print('total_hours',total_hours)
    # print('working_hours',working_hours)
    # time.sleep(10)
    return total_hours, working_hours


def roundOffLeaveCalculationUpdate(users, attendenceMonthMaster, leave_part_1_confirm, leave_part_2_not_cofirm,
                                   total_days, year_end_date, month_start, joining_date, cl, sl, el, al, is_joining_year=None):
    '''
        Leave Calculation on Monthly Basis [(32/365*No. Of Days in Month)]+Excess/Short Leaves in previous month
    '''
    try:

        # print("leave part 1", leave_part_1_confirm, "leave part 2 not confirm", leave_part_2_not_cofirm,
        #       "total days", total_days, "year_end_date", year_end_date, "month_start", month_start)
        # print(month_start, year_end_date)
        attendenceMonthMaster = AttendenceMonthMaster.objects.filter(month_start__date__gte=month_start,
                                                                     month_end__date__lte=year_end_date,
                                                                     is_deleted=False)

        # print('attendenceMonthMaster 1111111', attendenceMonthMaster)
        for user in users:
            # user = user.id
            for index, each_month in enumerate(attendenceMonthMaster):
                # print('index', index, type(index))
                # print("-------------------------",index)
                last = 0
                if (index + 1) == attendenceMonthMaster.count():
                    # print("in last step")
                    last = 1
                if index == 0:
                    excess_or_short_leaves_in_previous_month = 0
                    excess_or_short_leaves_in_previous_month_for_not_confirm = 0
                    excess_or_short_cl_in_previous_month = 0
                    excess_or_short_el_in_previous_month = 0
                    excess_or_short_sl_in_previous_month = 0
                    excess_or_short_al_in_previous_month = 0
                else:
                    attendenceLeaveAllocatePerMonthPerUser = AttendenceLeaveAllocatePerMonthPerUser.objects.get(
                        employee_id=user, month=(each_month.id - 1)
                    )
                    # print('attendenceLeaveAllocatePerMonthPerUser',attendenceLeaveAllocatePerMonthPerUser)
                    excess_or_short_leaves_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure)

                    excess_or_short_leaves_in_previous_month_for_not_confirm = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave_not_confirm -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure_not_confirm)

                    excess_or_short_cl_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_cl -
                            attendenceLeaveAllocatePerMonthPerUser.round_cl_allotted)
                    excess_or_short_el_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_el -
                            attendenceLeaveAllocatePerMonthPerUser.round_el_allotted)
                    excess_or_short_al_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_leave -
                            attendenceLeaveAllocatePerMonthPerUser.round_figure)
                    excess_or_short_sl_in_previous_month = (
                            attendenceLeaveAllocatePerMonthPerUser.net_monthly_sl -
                            attendenceLeaveAllocatePerMonthPerUser.round_sl_allotted)

                '''
                    Actual Round Off Calculation using Total Leave for any confirm employee
                '''

                total_leave = leave_part_1_confirm / total_days
                total_cl = cl / total_days
                total_el = el / total_days
                total_sl = sl / total_days
                total_al = al / total_days
                # print("--------",total_cl, total_el, total_sl)
                if not index and is_joining_year:
                    # print("in index and is join year true")
                    total_leave = (total_leave * (int(each_month.days_in_month) - int(joining_date.day)))
                    # if
                    total_al = (total_al * (int(each_month.days_in_month)))
                    total_sl = (total_sl * (int(each_month.days_in_month) - int(joining_date.day)))
                    total_el = (total_el * (int(each_month.days_in_month) - int(joining_date.day)))
                    total_cl = (total_cl * (int(each_month.days_in_month) - int(joining_date.day)))
                else:
                    total_leave = (total_leave * int(each_month.days_in_month))
                    total_al = (total_al * (int(each_month.days_in_month)))
                    total_sl = (total_sl * (int(each_month.days_in_month)))
                    total_el = (total_el * (int(each_month.days_in_month)))
                    total_cl = (total_cl * (int(each_month.days_in_month)))
                # print('total_leave', total_leave)
                leave_calculation = round(total_leave, 1)
                al_calculation = round(total_al, 1)
                cl_calculation = round(total_cl, 1)
                el_calculation = round(total_el, 1)
                sl_calculation = round(total_sl, 1)
                net_monthly_leave = leave_calculation + float(
                    excess_or_short_leaves_in_previous_month)  # For First Month
                cl_monthly_leave = cl_calculation + float(excess_or_short_cl_in_previous_month)  # For First Month
                el_monthly_leave = el_calculation + float(excess_or_short_el_in_previous_month)
                sl_monthly_leave = sl_calculation + float(excess_or_short_sl_in_previous_month)
                al_monthly_leave = al_calculation + float(excess_or_short_al_in_previous_month)
                round_figure_details = roundCustom(net_monthly_leave, last, leave_part_2_not_cofirm)
                # print("in this", last)
                if last:
                    # print("hfjkdshfjdhfdsjhfdjfhdsjfhdjfhsdjfhsjfhdsfjshfjshfdhkjsfhjfhdjfh")
                    # print("in last")
                    last = 0
                    # print(attendenceMonthMaster)
                    round_figure_cl_details = roundCustom(cl_monthly_leave, last, cl)
                    round_figure_el_details = roundCustom(el_monthly_leave, last, el)
                    round_figure_sl_details = roundCustom(sl_monthly_leave, last, sl)
                    # last = 0
                    round_figure_al_details = roundCustom(al_monthly_leave, last, al)
                    last = 1
                else:
                    # print("not in last")
                    round_figure_cl_details = roundCustom(cl_monthly_leave, last, cl)
                    round_figure_el_details = roundCustom(el_monthly_leave, last, el)
                    round_figure_sl_details = roundCustom(sl_monthly_leave, last, sl)
                    round_figure_al_details = roundCustom(al_monthly_leave, last, al)

                round_figure = round_figure_details['round_off']

                '''
                    Round Off Calculation using [leave_part_1] Leave for any not confirm employee
                '''
                total_leave1 = leave_part_2_not_cofirm / total_days
                total_leave1 = (total_leave1 * int(each_month.days_in_month))
                leave_cal_per_month_not_confirm = round(total_leave1, 1)
                net_monthly_leave_not_confirm = leave_cal_per_month_not_confirm + float(
                    excess_or_short_leaves_in_previous_month_for_not_confirm)  # For First Month
                round_figure_not_confirm_details = roundCustom(net_monthly_leave_not_confirm, last,
                                                               leave_part_2_not_cofirm)
                round_figure_not_confirm = round_figure_not_confirm_details['round_off']
                first_data = {
                    'employee_id': user,
                    'month': each_month,
                    'leave_cal_per_month': al_calculation,
                    'round_cl_allotted': round_figure_cl_details['round_off'],
                    'round_sl_allotted': round_figure_sl_details['round_off'],
                    'round_el_allotted': round_figure_el_details['round_off'],
                    # 'round_al_allotted': round_figure_al_details['round_off'],
                    'excess_or_short_leaves_in_previous_month': excess_or_short_al_in_previous_month,
                    "excess_or_cl_in_previous_month": excess_or_short_cl_in_previous_month,
                    "excess_or_el_in_previous_month":excess_or_short_el_in_previous_month,
                    "excess_or_sl_in_previous_month":excess_or_short_sl_in_previous_month,
                    'net_monthly_leave': al_monthly_leave,
                    'round_figure': round_figure_al_details['round_off'],
                    'leave_cal_per_month_not_confirm': al_calculation,
                    'excess_or_short_leaves_in_previous_month_for_not_confirm': excess_or_short_al_in_previous_month,
                    'net_monthly_leave_not_confirm': al_monthly_leave,
                    'round_figure_not_confirm': round_figure_al_details['round_off'],
                    'cl_allotted': cl_calculation,
                    'el_allotted': el_calculation,
                    'sl_allotted': sl_calculation,
                    'net_monthly_cl': cl_monthly_leave,
                    'net_monthly_el': el_monthly_leave,
                    'net_monthly_sl': sl_monthly_leave,
                    # 'al_allotted': al_calculation
                }
                # print(each_month)
                if AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee_id=user, month=each_month):
                    created = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(employee_id=user,
                                                                                    month=each_month).update(
                        leave_cal_per_month=al_calculation,
                        excess_or_short_leaves_in_previous_month=excess_or_short_al_in_previous_month,
                        net_monthly_leave=al_monthly_leave,
                        round_figure=round_figure_al_details['round_off'],
                        leave_cal_per_month_not_confirm=al_calculation,
                        excess_or_short_leaves_in_previous_month_for_not_confirm=excess_or_short_al_in_previous_month,
                        excess_or_cl_in_previous_month =excess_or_short_cl_in_previous_month,
                        excess_or_el_in_previous_month =excess_or_short_el_in_previous_month,
                        excess_or_sl_in_previous_month =excess_or_short_sl_in_previous_month,
                        net_monthly_leave_not_confirm=al_monthly_leave,
                        round_figure_not_confirm=round_figure_al_details['round_off'],
                        cl_allotted=cl_calculation,
                        el_allotted=el_calculation,
                        sl_allotted=sl_calculation,
                        # al_allotted= al_calculation,
                        round_cl_allotted=round_figure_cl_details['round_off'],
                        round_sl_allotted=round_figure_sl_details['round_off'],
                        round_el_allotted=round_figure_el_details['round_off'],
                        net_monthly_cl= cl_monthly_leave,
                        net_monthly_el= el_monthly_leave,
                        net_monthly_sl= sl_monthly_leave,
                        # round_al_allotted= round_figure_al_details['round_off']

                    )
                else:
                    cc, created = AttendenceLeaveAllocatePerMonthPerUser.objects.get_or_create(
                        **first_data
                    )

                # print("month wise updated")
                #     **first_data
                # )

    except Exception as e:
        raise APIException({
            'request_status': 0,
            'msg': e
        })


