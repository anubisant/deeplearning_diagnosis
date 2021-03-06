# coding=utf-8
import datetime
import copy
import random


def predict_vm(ecs_lines, input_lines):
    # Do your work from here#
    result = []
    if ecs_lines is None:
        print
        'ecs information is none'
        return result
    if input_lines is None:
        print
        'input file information is none'
        return result

    # transform the trianing data to matrix

    # print date_list
    data_tran = trans_data(ecs_lines)

    # tansform the input txt to the wanted condition
    input_condition = []
    for line in input_lines:
        sub_list = line.split(' ')
        input_condition.append(sub_list)

    # the configration of physical server
    server_info = [int(input_condition[0][0]), int(input_condition[0][1])]

    # the flavor to be predicted
    input_flavor_num = int(input_condition[1][0])
    flavor_info = input_condition[2:2 + input_flavor_num]
    flavor_name = [flavor[0] for flavor in flavor_info]
    flavor_name_int = [int(flavor[6:]) for flavor in flavor_name]  # need a sort
    cpu_use_list = [int(flavor[1]) for flavor in flavor_info]
    mem_use_list = [int(int(flavor[2]) / 1024) for flavor in flavor_info]
    flavor_list = []
    for i in range(len(flavor_name)):
        flavor_list.append([flavor_name[i], cpu_use_list[i], mem_use_list[i]])
    flavor_cpu_dict = {}
    flavor_mem_dict = {}
    for i in range(len(flavor_name)):
        flavor_cpu_dict[flavor_name[i]] = cpu_use_list[i]
        flavor_mem_dict[flavor_name[i]] = mem_use_list[i]
    print(flavor_cpu_dict, flavor_mem_dict)

    # print flavor_list

    # the optimiztion dim
    optimize_dim = input_condition[2 + input_flavor_num][0]

    # prognosis start and end
    prog_start = datetime.datetime.strptime(input_condition[3 + input_flavor_num][0], '%Y-%m-%d')
    prog_end = datetime.datetime.strptime(input_condition[4 + input_flavor_num][0], '%Y-%m-%d')
    day_dur = (prog_end - prog_start).days + 1

    # predict stage
    flavor_pre_sum = []  #
    train_data_used = data_tran[-day_dur - 1:-1]
    for i in range(1, len(data_tran[0])):
        item_mean = sum([data[i] for data in train_data_used])
        item_mean = int(item_mean)
        flavor_pre_sum.append(item_mean)
    flavor_pre_used = [flavor_pre_sum[index - 1] for index in flavor_name_int]
    print(sum(flavor_pre_used))
    best_score = 0.0
    for i in range(len(flavor_list)):
        flavor_list[i].append(flavor_pre_used[i])
    list_num_flavor = []
    for flavor in flavor_list:
        for i in range(flavor[3]):
            list_num_flavor.append(flavor[0])
    print(list_num_flavor)
    # server_list = copy.deepcopy(best_server_list)
    # server_num = len(server_list)

    pre_used_sum = sum([flavor[3] for flavor in flavor_list])  # sum of predicted flavor

    # put the flavors into physical server
    result.append(pre_used_sum)
    for i in range(len(flavor_pre_used)):
        flavor_str = flavor_list[i][0] + ' ' + str(flavor_list[i][3])
        result.append(flavor_str)
    result.append('')
    # result.append(server_num)
    index = 1
    # for server in server_list:
    #     server_str = str(index)
    #     for flavor in flavor_list:
    #         if flavor[0] in server.keys():
    #             server_str = server_str + ' ' + flavor[0] + ' ' + str(server[flavor[0]])
    #     index = index + 1
    #     result.append(server_str)
    # return result


def trans_data(data_lines):
    date_list = []
    data_list = []
    for record in data_lines:
        record_seperate = record.split()
        record_date = record_seperate[2][:10]
        record_value = int(record_seperate[1][6:])
        line_data_and_value = [record_date, record_value]
        data_list.append(line_data_and_value)
        date_list.append(record_date)
    date_list = sorted(set(date_list), key=date_list.index)
    data_tran = []
    for date in date_list:
        sub_date = [date]
        for i in range(15):  # struct the matrix,the matrix have 16 column
            sub_date.append(0)
        data_tran.append(sub_date)

    curren_index = 0  # index of date,if date changes,index plus 1
    for i in range(len(data_list)):
        if i == 0:
            data_tran[curren_index][data_list[i][1]] = data_tran[curren_index][data_list[i][1]] + 1
        else:
            if data_list[i][0] == data_list[i - 1][0]:
                if data_list[i][1] <= 15:
                    data_tran[curren_index][data_list[i][1]] = data_tran[curren_index][data_list[i][1]] + 1
                else:
                    pass
            else:
                curren_index = curren_index + 1
                if data_list[i][1] <= 15:
                    data_tran[curren_index][data_list[i][1]] = data_tran[curren_index][data_list[i][1]] + 1
                else:
                    pass
    return data_tran


def tuihuo(server_config, list_num_flavor, flavor_mem_dict, flavor_cpu_dict):
    server = [server_config[0], server_config[1]]
    server_list = []
    for i in range(10000):
        exchange_index1, exchange_index2 = generate_random_int(0, len(list_num_flavor) - 1)
        list_num_flavor[exchange_index1], list_num_flavor[exchange_index2] = list_num_flavor[exchange_index2], \
                                                                             list_num_flavor[exchange_index1]
        for i in range(len(list_num_flavor)):
            if server_list == []:
                server_copy = copy.deepcopy(server)
                server_list.append(server_copy)
            place = False
            for server in server_list:
                if server[0] > flavor_cpu_dict[list_num_flavor[i]] and server[1] > flavor_mem_dict[list_num_flavor[i]]:
                    server[0] -= flavor_cpu_dict[list_num_flavor[i]]
                    server[1] -= flavor_mem_dict[list_num_flavor[i]]
                    server.append(list_num_flavor[i])
                    place = True
            if place == False:
                new_server = [server[0]-flavor_cpu_dict[list_num_flavor[i]],server[1]-server[0]-flavor_cpu_dict[list_num_flavor[i]]]
                new_server.append(list_num_flavor[i])
                server_list.append(new_server)
    return server_list



def place_flavor_with_shuffle(server_config, flavor_list):
    for time in range(1000):
        flavor_list_copy = copy.deepcopy(flavor_list)
        server_list = []
        while sum([flavor[3] for flavor in flavor_list_copy]) > 0:
            cpu_remain = server_config[0]
            mem_remain = server_config[1]
            server_flavor = {}
            while (cpu_remain > 0 and mem_remain > 0):
                left = False
                for flavor in flavor_list_copy:
                    if flavor[3] > 0 and cpu_remain > flavor[1] and mem_remain > flavor[2]:
                        left = True
                if left == False:
                    break
                i = len(flavor_list_copy) - 1
                random.shuffle(flavor_list_copy)
                while i >= 0:
                    if flavor_list_copy[i][3] > 0 and cpu_remain > flavor_list_copy[i][1] and mem_remain > \
                            flavor_list_copy[i][2]:
                        if flavor_list_copy[i][0] not in server_flavor.keys():
                            server_flavor[flavor_list_copy[i][0]] = 0
                        server_flavor[flavor_list_copy[i][0]] += 1
                        cpu_remain -= flavor_list_copy[i][1]
                        mem_remain -= flavor_list_copy[i][2]
                        flavor_list_copy[i][3] = flavor_list_copy[i][3] - 1
                    i = i - 1
            server_list.append(server_flavor)
        if time == 0:
            best_list = server_list
        else:
            if len(best_list) > len(server_list):
                best_list = server_list
    return best_list


def place_envaluate(server_config, optim_dim, sever_num, flavor_list):
    if optim_dim == 'cpu':
        cpu_use = sum([flavor[1] * flavor[3] for flavor in flavor_list])
        utilization = cpu_use / (sever_num * server_config[0])
    else:
        mem_use = sum([flavor[2] * flavor[3] for flavor in flavor_list])
        utilization = mem_use / (sever_num * server_config[1])
    return utilization


def generate_random_int(min, max):
    first_random_int = random.randint(min, max)
    second_random_int = random.randint(min, max)
    while first_random_int == second_random_int:
        second_random_int = random.randint(min, max)
    return first_random_int, second_random_int
