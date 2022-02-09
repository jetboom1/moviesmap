import folium
from haversine import haversine
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import argparse
from geopy.exc import GeocoderUnavailable

main_map = folium.Map()
geolocator = Nominatim(user_agent='main.py')
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def find_possible_movies(user_coords, user_year, path_to_file):
    """
    Finds suitable movies and returns a list of sorted-by-nearest movies to user location
    :param user_coords: e.g. '49.83826, 24.02324'
    :param user_year: e.g '2002'
    :param path_to_file: '.\locations.list'
    :return: list of tuples (title, year, coords, distance_to_user)
    """
    with open(path_to_file, 'r') as file:
        line_num = 0
        movie_pack = []
        output = []
        cache = {}
        for line in file:
            line_num += 1
            line = line[:-1]
            if str(user_year) in line and 125000 < line_num <= 150000:
                packed = list(filter(lambda a: a != '', line.split('\t')))
                body, location = packed[0], packed[1]
                if body.find('"') != -1:
                    title = body[1:body[1:].find('"') + 1]
                else:
                    title = body[:body.find('(')].strip()
                obj = (title, user_year, location)
                if obj not in movie_pack:
                    movie_pack.append(obj)
    for movie in movie_pack:
        try:
            if movie[2] in cache.keys():
                distance_to_user = cache[movie[2]][0]
                coord1, coord2 = cache[movie[2]][1]
            else:
                coords = geolocator.geocode(movie[2])
                coord1, coord2 = coords.latitude, coords.longitude
                distance_to_user = haversine(map(float, user_coords.split(', ')), (coord1, coord2))
                cache[movie[2]] = (distance_to_user, (coord1, coord2))
            if distance_to_user > 2000:
                continue
            output.append([movie[0], user_year, (coord1, coord2), distance_to_user])
        except AttributeError:
            continue
        except GeocoderUnavailable:
            continue
    return sorted(output, key=lambda a: a[-1])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('year', type=int,
                        help='Year for what we`re builing the map')
    parser.add_argument('coord1', help='Your latitude (e.g 49.83826)')
    parser.add_argument('coord2', help='Your longitude (e.g 24.02324)')
    args = parser.parse_args()
    # year = input("Please enter a year you would like to have a map for:")
    # user_coords = input("Please enter your location (format: lat, long):")
    # print('Please wait!')
    user_coords = ', '.join([args.coord1, args.coord2])
    closest_movies = find_possible_movies(user_coords, args.year, 'locations.list')
    coords_cache = []
    childs = 0
    for movie_index in range(100):
        try:
            movie = closest_movies[movie_index]
        except IndexError:
            break
        if childs >= 10:
            break
        if movie[2] in coords_cache:
            continue
        else:
            coords_cache.append(movie[2])
            main_map.add_child(folium.Marker(location=movie[2], popup=movie[0],
                                             icon=folium.Icon(color="green", icon_color="yellow", icon="camera")))
            childs += 1
    main_map.add_child(folium.Marker(location=user_coords.split(', '), popup='You are here',
                                     icon=folium.Icon(color='red', icon_color='blue', icon='home')))
    main_map.add_child(folium.features.ClickForMarker(popup="You`ve clicked here"))
    main_map.save('map.html')
    print('Done! Check result in /map.html')
