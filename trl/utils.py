import re
from word2number import w2n

from .annotations import (num_rooms_annotation,
                          adjacency_annotations,
                          location_annotations)

regex = re.compile(".*?\((.*?)\)")

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
  
def house_bbox(polygons):
    bounds = [polygon.bounds for polygon in polygons]
    
    xmin = np.array(bounds)[:, 0].min()
    ymin = np.array(bounds)[:, 1].min()
    xmax = np.array(bounds)[:, 2].max()
    ymax = np.array(bounds)[:, 3].max()
    
    return xmin, xmax, ymin, ymax

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
  
def get_layout_details(lm_generation, prompt):
    geom = []
    new_spaces = []
    new_space_ids = []
    fail=0
    gfa = dict.fromkeys([prompt])
    temp = dict()
    layout = lm_generation.lower().lstrip().replace('<|endoftext|>', '').rstrip().split(', ')
    spaces = [txt.split(':')[0].replace('living_room', 'livingroom') for txt in layout]
    space_numbers = Counter(spaces)
    space_ids = [get_value(housegan_labels, space) for space in spaces if(type(get_value(housegan_labels, space)) == int)]
    coordinates = [txt.split(':')[1].lstrip() for txt in layout]
    coordinates = [re.findall(regex, coord) for coord in coordinates]
    coordinates = [x for x in coordinates if x != []]

    polygons = []
    for coord in coordinates:
        polygons.append([point.split(',') for point in coord])
    for poly, space, space_id in zip(polygons, spaces, space_ids):
        poly = [x for x in poly if x != ['']]
        poly = [x for x in poly if '' not in x]
        try:
            geom.append(Polygon(np.array(poly, dtype=int)))
            new_spaces.append(space)
            new_space_ids.append(space_id)
        except:
            fail=1 
    if(fail==1):
        failed+=1
    else:
        cleaned = [(g, space, id_) for g, space, id_ in zip(geom, new_spaces, new_space_ids) if g.area>0]
        geom = [clean[0] for clean in cleaned]
        spaces = [clean[1] for clean in cleaned]
        space_ids = [clean[2] for clean in cleaned]

    vectors = []
    xmin, xmax, ymin, ymax = house_bbox(geom)
    center_point = xmin+((xmax - xmin)/2), ymin+((ymax-ymin)/2)

    room_coords = np.concatenate([poly.centroid.xy for poly in geom])
    room_y = room_coords[0::2]
    room_x = room_coords[1::2]
    room_centroids = np.hstack([room_x, room_y])

    for centroid in room_centroids:
        vectors.append([center_point[0]-centroid[0], center_point[1]-centroid[1]])
        
    for geo, space in zip(geom, spaces):
        add_and_increment(temp, space, geo.area)
        add_and_increment(temp, space+'_avg', geo.area / space_numbers[space])
        
    for key in gfa.keys():
        gfa[key] = temp
        
    return spaces, geom, vectors, gfa

def get_layout_accuracy(spaces, geom, vectors, prompt):
    n_descriptions, a_descriptions, l_descriptions = dict(), dict(), dict()
    annotations = []
    accuracy = []
    num_desc = num_rooms_annotation(spaces)
    for desc in list(flatten(num_desc)):
        add_and_increment(n_descriptions, desc, increment=1)
    annotations.extend(list(set(flatten(num_desc))))
    adj_desc = adjacency_annotations(spaces, geom)
    for desc in list(flatten(adj_desc)):
        add_and_increment(a_descriptions, desc, increment=1)
    annotations.extend(list(set(flatten(adj_desc))))
    loc_desc = location_annotations(spaces, vectors)
    for desc in list(flatten(loc_desc)):
        add_and_increment(l_descriptions, desc, increment=1)
    annotations.extend(list(set(flatten(loc_desc))))

    annotations = [re.sub('_', ' ', d) for d in annotations]
    """
    if "adjacent to" in prompt:
        prompt_a = 'a ' + ' '.join(prompt.split(' ')[1:]).lower()
        prompt_b = 'the ' + ' '.join(prompt.split(' ')[1:]).lower()
        accuracy.append((prompt_a in annotations) | (prompt_b in annotations))
    else:
        accuracy.append(prompt in annotations)
    """
    accuracy.append(prompt in annotations)
    return accuracy, annotations, n_descriptions, a_descriptions, l_descriptions
  
def get_room_distances(prompt, spaces):
    nbed, nbath, nrooms, bedd, bathd, avg_bb_distance, room_distance = None, None, None, None, None, None, None
    lbed = prompt.find('bedroom')
    lbath = prompt.find('bathroom')
    lrooms = prompt.find(' rooms')
    if(lbed>0):
        nbed = w2n.word_to_num(prompt[:lbed].rstrip().split(' ')[-1])
    if(lbath>0):
        nbath = w2n.word_to_num(prompt[:lbath].rstrip().split(' ')[-1])
    if(lrooms>0):
        nrooms = w2n.word_to_num(prompt[:lrooms].rstrip().split(' ')[-1])
        
    if(nbed and nbath):
        gen_bed = np.where(np.array(spaces) == 'bedroom')[0].shape[0]
        gen_bath = np.where(np.array(spaces) == 'bathroom')[0].shape[0]
        bedd = nbed - gen_bed
        bathd = nbath - gen_bath
        avg_bb_distance = (abs(bedd) + abs(bathd)) / 2
    if(nrooms):
        room_distance = len(spaces) - nrooms

    return bedd, bathd, avg_bb_distance, room_distance
