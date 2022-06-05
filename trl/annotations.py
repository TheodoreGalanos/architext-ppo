import num2word

def angle_between(a,b):
    dot = a[0]*b[0] + a[1]*b[1]      # dot product between [x1, y1] and [x2, y2]
    det = a[0]*b[1] - a[1]*b[0]      # determinant
    angle = atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
    
    return np.rad2deg(angle)
  
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
  


# get locations of rooms
def location_annotations(spaces, vectors):
    init_vector = [0,-1]
    desc = []
    loc_descriptions = []
    
    #kept_spaces = ["livingroom", "kitchen", "bedroom", "bathroom", "dining_room", "corridor"]
    nbed = np.where(np.array(spaces) == 'bedroom')[0].shape[0]
    nbath = np.where(np.array(spaces) == 'bathroom')[0].shape[0]
    
    for space, vector in zip(spaces, vectors):
        angle = int(angle_between(vector, init_vector))
        if(angle>0):
            cond = [(angle >= int(orientation[0])) & (angle <= int(orientation[1])) for orientation in room_angles]
        else:
            cond = [(angle <= int(orientation[0])) & (angle >= int(orientation[1])) for orientation in room_angles]
        loc = room_orientations[cond][0]
        if(space in ['kitchen', 'livingroom', 'corridor']):
            loc_descriptions.append('the %s is located in the %s side of the house' % (space, loc))
        elif(space=='bathroom'):
            if(nbath==1):
                loc_descriptions.append('the %s is located in the %s side of the house' % (space, loc))
            else:
                loc_descriptions.append('a %s is located in the %s side of the house' % (space, loc))
        elif(space=='bedroom'):
            if(nbed==1):
                loc_descriptions.append('the %s is located in the %s side of the house' % (space, loc))
            else:
                loc_descriptions.append('a %s is located in the %s side of the house' % (space, loc))

    desc.append(list(set(flatten(loc_descriptions))))
    
    return desc
  
  # get room-based annotations
  def num_rooms_annotation(spaces):
    
    desc = []
    nbed = np.where(np.array(spaces) == 'bedroom')[0].shape[0]
    nbath = np.where(np.array(spaces) == 'bathroom')[0].shape[0]

    desc.append("a house with %s rooms" % num2word.word(len(spaces)).lower())

    if((nbed > 1) & ((nbath) > 1)):
        desc.append("a house with %s bedrooms and %s bathrooms" % (num2word.word(nbed).lower(), num2word.word(nbath).lower()))
    elif((nbed > 1) & ((nbath) == 1)):
        desc.append("a house with %s bedrooms and one bathroom" % (num2word.word(nbed).lower()))
    elif((nbed == 1) & ((nbath) > 1)):
        desc.append("a house with one bedroom and %s bathrooms" % (num2word.word(nbath).lower()))
    elif((nbed == 1) & ((nbath) == 1)):
        desc.append("a house with one bedroom and one bathroom")
    elif(len(spaces)==1):
        desc.append("a house with one room")
    elif(nbath == 0):
        if(nbed > 1):
            desc.append("a house with %s bedrooms and no bathroom" % (num2word.word(nbed).lower()))
        elif(nbed==0):
            desc.append("a house with no bedroom and no bathroom")
        else:
            desc.append("a house with one bedroom and no bathroom")
    elif(nbed == 0):
        if(nbath > 1):
            desc.append("a house with no bedroom and %s bathrooms" % (num2word.word(nbath).lower()))
        elif(nbath == 0):
            desc.append("a house with no bedroom and no bathroom")
        else:
            desc.append("a house with no bedroom and one bathroom")
    else:
        desc.append("a house with %s bedrooms and %s bathrooms" % (num2word.word(nbed).lower(), 
                                                                        num2word.word(nbath).lower()))
    return desc
  
# get adjacency-based annotations
def adjacency_annotations(spaces, polygons):
    desc = []
    adj_desc = []
    kitchen_adj = []
    living_adj = []
    bathroom_adj = []
    bedroom_adj = []
    kitchen_nonadj = []
    living_nonadj = []
    bathroom_nonadj = []
    bedroom_nonadj = []
    scaled_polygons = []
    
    kept_spaces = ["livingroom", "kitchen", "bedroom", "bathroom", "corridor"]
    nbed = np.where(np.array(spaces) == 'bedroom')[0].shape[0]
    nbath = np.where(np.array(spaces) == 'bathroom')[0].shape[0]
    
    for polygon in polygons:
        scaled_polygons.append(scale(polygon, 1.15, 1.15, origin=polygon.centroid))
    intersection_matrix = np.zeros((len(scaled_polygons), len(scaled_polygons)))
    for k, p in enumerate(scaled_polygons):
        intersection_matrix[:, k] = find_intersections(p, scaled_polygons)
    for j, space in enumerate(spaces):
        if space in kept_spaces:
            adj_spaces = np.array(spaces)[intersection_matrix[j].astype(bool)]
            adj_spaces = [s for s in adj_spaces if s in kept_spaces]
            adj_spaces = set(adj_spaces)
            adj_spaces.remove(space)
            non_adj_spaces = np.array(spaces)[~intersection_matrix[j].astype(bool)]
            non_adj_spaces = [s for s in non_adj_spaces if s in kept_spaces]
            non_adj_spaces = set(non_adj_spaces)
            try:
                non_adj_spaces.remove(space)
            except:
                pass
            if('kitchen' in list(adj_spaces)):
                if(space=='livingroom'):
                    kitchen_adj.append('the %s is adjacent to the kitchen' % (space))
                elif(space=='bedroom'):
                    if(nbed==1):
                        kitchen_adj.append('the %s is adjacent to the kitchen' % (space))
                    else:
                        kitchen_adj.append('a %s is adjacent to the kitchen' % (space))
                elif(space=='bathroom'):
                    if(nbath==1):
                        kitchen_adj.append('the %s is adjacent to the kitchen' % (space))
                    else:
                        kitchen_adj.append('a %s is adjacent to the kitchen' % (space))
                else:
                    pass
            if('livingroom' in list(adj_spaces)):
                if(space=='kitchen'):
                    living_adj.append('the %s is adjacent to the livingroom' % (space))
                elif(space=='bedroom'):
                    if(nbed==1):
                        living_adj.append('the %s is adjacent to the livingroom' % (space))
                    else:
                        living_adj.append('a %s is adjacent to the livingroom' % (space))
                elif(space=='bathroom'):
                    if(nbath==1):
                        living_adj.append('the %s is adjacent to the livingroom' % (space))
                    else:
                        living_adj.append('a %s is adjacent to the livingroom' % (space))
                else:
                    pass
            if('bedroom' in list(adj_spaces)):
                if(nbed==1):
                    if(space=='livingroom'):
                        bedroom_adj.append('the %s is adjacent to the bedroom' % (space))
                    elif(space=='kitchen'):
                        bedroom_adj.append('the %s is adjacent to the bedroom' % (space))
                    elif(space=='bathroom'):
                        if(nbath==1):
                            bedroom_adj.append('the %s is adjacent to the bedroom' % (space))
                        else:
                            bedroom_adj.append('a %s is adjacent to the bedroom' % (space))
                else:
                    if(space=='livingroom'):
                        bedroom_adj.append('the %s is adjacent to a bedroom' % (space))
                    elif(space=='kitchen'):
                        bedroom_adj.append('the %s is adjacent to a bedroom' % (space))
                    elif(space=='bathroom'):
                        if(nbath==1):
                            bedroom_adj.append('the %s is adjacent to a bedroom' % (space))
                        else:
                            bedroom_adj.append('a %s is adjacent to a bedroom' % (space))
                    else:
                        pass
            if('bathroom' in list(adj_spaces)):
                if(nbath==1):
                    if(space == 'kitchen'):
                        bathroom_adj.append('the %s is adjacent to the bathroom' % (space))
                    elif(space == 'livingroom'):
                        bathroom_adj.append('the %s is adjacent to the bathroom' % (space))
                    elif(space=='bedroom'):
                        if(nbed==1):
                            bathroom_adj.append('the %s is adjacent to the bathroom' % (space))
                        else:
                            bathroom_adj.append('a %s is adjacent to the bathroom' % (space))
                else:
                    if(space=='kitchen'):
                        bathroom_adj.append('the %s is adjacent to a bathroom' % (space))
                    elif(space=='livingroom'):
                        bathroom_adj.append('the %s is adjacent to a bathroom' % (space))
                    elif(space=='bedroom'):
                        if(nbed==1):
                            bathroom_adj.append('the %s is adjacent to a bathroom' % (space))
                        else:
                            bathroom_adj.append('a %s is adjacent to a bathroom' % (space))

            if('kitchen' in list(non_adj_spaces)):
                if(space=='livingroom'):
                    kitchen_nonadj.append('the %s is not adjacent to the kitchen' % (space))
                elif(space=='bedroom'):
                    if(nbed==1):
                        kitchen_nonadj.append('the %s is not adjacent to the kitchen' % (space))
                    else:
                        kitchen_nonadj.append('a %s is not adjacent to the kitchen' % (space))
                elif(space=='bathroom'):
                    if(nbath==1):
                        kitchen_nonadj.append('the %s is not adjacent to the kitchen' % (space))
                    else:
                        kitchen_nonadj.append('a %s is not adjacent to the kitchen' % (space))
                else:
                    pass
            if('livingroom' in list(non_adj_spaces)):
                if(space=='kitchen'):
                    living_nonadj.append('the %s is not adjacent to the livingroom' % (space))
                elif(space=='bedroom'):
                    if(nbed==1):
                        living_nonadj.append('the %s is not adjacent to the livingroom' % (space))
                    else:
                        living_nonadj.append('a %s is not adjacent to the livingroom' % (space))
                elif(space=='bathroom'):
                    if(nbath==1):
                        living_nonadj.append('the %s is not adjacent to the livingroom' % (space))
                    else:
                        living_nonadj.append('a %s is not adjacent to the livingroom' % (space))
            if('bathroom' in list(non_adj_spaces)):
                if(nbath==1):
                    if(space=='kitchen'):
                        bathroom_nonadj.append('the %s is not adjacent to the bathroom' % (space))
                    elif(space=='livingroom'):
                        bathroom_nonadj.append('the %s is not adjacent to the bathroom' % (space))
                    elif(space=='bedroom'):
                        if(nbed==1):
                            bathroom_nonadj.append('the %s is not adjacent to the bathroom' % (space))
                        else:
                            bathroom_nonadj.append('a %s is not adjacent to the bathroom' % (space))
                else:
                    if(space=='kitchen'):
                        bathroom_nonadj.append('the %s is not adjacent to a bathroom' % (space))
                    elif(space=='livingroom'):
                        bathroom_nonadj.append('the %s is not adjacent to a bathroom' % (space))
                    elif(space=='bedroom'):
                        if(nbed==1):
                            bathroom_nonadj.append('the %s is not adjacent to a bathroom' % (space))
                        else:
                            bathroom_nonadj.append('a %s is not adjacent to a bathroom' % (space))
            if('bedroom' in list(non_adj_spaces)):
                if(nbed==1):
                    if(space=='livingroom'):
                        bedroom_nonadj.append('the %s is not adjacent to the bedroom' % (space))
                    elif(space=='kitchen'):
                        bedroom_nonadj.append('the %s is not adjacent to the bedroom' % (space))
                    elif(space=='bathroom'):
                        if(nbath==1):
                            bedroom_nonadj.append('the %s is not adjacent to the bedroom' % (space))
                        else:
                            bedroom_nonadj.append('a %s is not adjacent to the bedroom' % (space))
                else:
                    if(space=='livingroom'):
                        bedroom_nonadj.append('the %s is not adjacent to a bedroom' % (space))
                    elif(space=='kitchen'):
                        bedroom_nonadj.append('the %s is not adjacent to a bedroom' % (space))
                    elif(space=='bathroom'):
                        if(nbath==1):
                            bedroom_nonadj.append('the %s is not adjacent to a bedroom' % (space))
                        else:
                            bedroom_nonadj.append('a %s is not adjacent to a bedroom' % (space))
            else:
                pass


    adj_lists = [kitchen_adj, living_adj, bathroom_adj, bedroom_adj]
    nadj_lists = [kitchen_nonadj, living_nonadj, bathroom_nonadj, bedroom_nonadj]
    for l in adj_lists:
        if(len(l)):
            adj_desc.append(list(set(l)))
    for l in nadj_lists:
        if(len(l)):
            adj_desc.append(list(set(l)))

    desc.append(list(set(flatten(adj_desc))))
    
    return desc
