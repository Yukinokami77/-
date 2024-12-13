import os

def read_routes(input_file):
    routes = {}
    reverse_routes = {}
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(';')
            if len(parts) < 3:
                continue
            building_id, address, next_building = parts
            routes[building_id] = (address, next_building)
            if next_building:
                reverse_routes[next_building] = building_id
    return routes, reverse_routes

def find_start_points(routes, reverse_routes):
    start_points = []
    for building_id in routes:
        if building_id not in reverse_routes:
            start_points.append(building_id)
    return start_points

def construct_route(start_id, routes):
    route = []
    current_id = start_id
    while current_id:
        address, next_id = routes[current_id]
        route.append(address)
        current_id = next_id
    return route

def find_longest_route(routes, reverse_routes):
    start_points = find_start_points(routes, reverse_routes)
    longest_route = []
    for start_id in start_points:
        route = construct_route(start_id, routes)
        if len(route) > len(longest_route):
            longest_route = route
    return longest_route

def write_output(output_file, longest_route):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(' -> '.join(longest_route))
        print(' -> '.join(longest_route))


input_file = 'input.txt'
output_file = 'output.txt'

routes, reverse_routes = read_routes(input_file)
longest_route = find_longest_route(routes, reverse_routes)
write_output(output_file, longest_route)
print("Результат сохранен в output.txt")
os.system("pause")

