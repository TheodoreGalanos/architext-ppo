


housegan_labels = {"livingroom": 1, "kitchen": 2, "bedroom": 3, "bathroom": 4, "missing": 5, "closet": 6, 
                         "balcony": 7, "corridor": 8, "dining_room": 9, "laundry_room": 10}

location_adjacencies = {'north': ['north east', 'north west'],
                        'north west': ['north', 'west'],
                        'west': ['north west', 'south west'],
                        'south west': ['west', 'south'],
                        'south': ['south west', 'south east'],
                        'south east': ['south', 'east'],
                        'east': ['south east', 'north east'],
                        'north east': ['north', 'east']}

room_orientations = np.array(['north', 
                              'north east', 
                              'east', 
                              'south east', 
                              'south', 
                              'south',       
                              'south west', 
                              'west', 
                              'north west', 
                              'north'], dtype=str)

room_angles = np.array([[0, 22.5], 
                     [22.5, 67.5], 
                     [67.5, 112.5], 
                     [112.5, 157.5], 
                     [157.5, 180], 
                     [-157.5, -180],
                     [-112.5, -157.5],                    
                     [-67.5, -112.5],
                     [-22.5, -67.5],
                     [0, -22.5]], dtype=float)

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el
           
def add_and_increment(dictionary, key, increment):
    if key in dictionary:
        dictionary[key] += increment
    else:
        dictionary[key] = increment
    return dictionary

def get_value(dictionary, val):
    for key, value in dictionary.items():
        if val == key:
            return value

def angle_between(a,b):
    dot = a[0]*b[0] + a[1]*b[1]      # dot product between [x1, y1] and [x2, y2]
    det = a[0]*b[1] - a[1]*b[0]      # determinant
    angle = atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
    
    return np.rad2deg(angle)
  


def house_bbox(polygons):
    bounds = [polygon.bounds for polygon in polygons]
    
    xmin = np.array(bounds)[:, 0].min()
    ymin = np.array(bounds)[:, 1].min()
    xmax = np.array(bounds)[:, 2].max()
    ymax = np.array(bounds)[:, 3].max()
    
    return xmin, xmax, ymin, ymax

def find_intersections(seed_polygon, target_polygons):
    """
        A function that finds intersections between a seed polygon and a list of candidate polygons.

    Args:
        seed_polygon (shapely polygon): A shapely polygon.
        target_polygons (list): A list of shapely polygons.

    Returns:
        array: The intersection matrix between the seed polygon and all individual target polygons.
    """
    intersect_booleans = []
    for _, poly in enumerate(target_polygons):
        try:
            intersect_booleans.append(seed_polygon.intersects(poly))
        except:
            intersect_booleans.append(True)
    return intersect_booleans

def get_location_distances(prompt, desc):
    req_location = prompt.split('is located in the ')[1].split(' side')[0]
    search_loc = prompt.split('is located in the ')[0].split(' ')[1]
    gen_location = [d for d in desc if 'side of the house' in d]
    gen_location = [loc for loc in gen_location if search_loc in loc]
    gen_cell = gen_location[0].split('is located in the ')[1].split(' side')[0]
    adj_cells = location_adjacencies[req_location]
    if(gen_cell == req_location):
        location_distance=0
    elif(gen_cell in adj_cells):
        location_distance=1
    else:
        location_distance=2
    return location_distance
