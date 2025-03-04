def get_id(value):
    values_int_only = []

    for sublist in value:
        if sublist and sublist[0].isdigit():
            values_int_only.append(int(sublist[0]))

    if values_int_only:
        return max(values_int_only) + 1
    else:
        return 1

if __name__ == '__main__':
    get_id()