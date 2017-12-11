# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
import numpy as np
import pandas as pd
import json
from django.core.serializers.json import DjangoJSONEncoder


# Create your views here.
def index(request):
    """
    View function for home page of site.
    """
    # Render the HTML template index.html with the data in the context variable
    if request.method == "POST":
        cluster, centroid = process_data(dict(request.POST))
        housing = process_idealista(dict(request.POST), cluster)
        cluster_centroid, ids, prices, sizes, num_bedrooms, num_bathrooms, districts, links = \
            process_housing(housing, centroid)
        print(cluster_centroid)
        return render(
            request,
            'retrieve_housing.html',
            context={
                'cluster': json.dumps(list(cluster), cls=DjangoJSONEncoder),
                'centroid': json.dumps(list(cluster_centroid), cls=DjangoJSONEncoder),
                'ids': json.dumps(list(ids), cls=DjangoJSONEncoder),
                'prices': json.dumps(list(prices), cls=DjangoJSONEncoder),
                'sizes': json.dumps(list(sizes), cls=DjangoJSONEncoder),
                'num_bedrooms': json.dumps(list(num_bedrooms), cls=DjangoJSONEncoder),
                'num_bathrooms': json.dumps(list(num_bathrooms), cls=DjangoJSONEncoder),
                'districts': json.dumps(list(districts), cls=DjangoJSONEncoder),
                'links': json.dumps(list(links), cls=DjangoJSONEncoder),
             },
        )

    return render(
        request,
        'index.html',
        context={},
    )


def process_housing(housing, centroid):
    cluster_centroid, ids, prices, sizes, num_bedrooms, num_bathrooms, districts, links = [], [], [], [], [], [], [], []
    for i in range(len(centroid)):
        print(centroid[i])
        cluster_centroid.append(unicode(str(centroid[i])))
    for houses in housing:
        ids.append(unicode(houses[-1].split('/')[-1]))
        prices.append(unicode(houses[4]))
        sizes.append(unicode(houses[5]))
        num_bedrooms.append(unicode(houses[2]))
        num_bathrooms.append(unicode(houses[3]))
        districts.append(houses[1])
        links.append(houses[-1])
    return cluster_centroid, ids, prices, sizes, num_bedrooms, num_bathrooms, districts, links


def process_idealista(submission, cluster):
    # reading files
    idealista = pd.read_csv('catalog/data/idealista_data.csv').values
    price_min = int(submission['price_min'][0])
    price_max = int(submission['price_max'][0])
    size_min = int(submission['size_min'][0])
    size_max = int(submission['size_max'][0])
    number_of_bedrooms = int(submission['number_of_bedrooms'][0])
    number_of_bathrooms = int(submission['number_of_bathrooms'][0])
    if price_min > price_max:
        price_min, price_max = price_max, price_min
    if size_min > size_max:
        size_min, size_max = size_max, size_min
    # selection
    idealista_cluster = []
    for district in idealista:
        for i in cluster:
            if district[0] == i:
                idealista_cluster.append(district)
                break
    idealista_cluster = np.array(idealista_cluster)
    if number_of_bedrooms < 4:
        idealista_cluster = idealista_cluster[idealista_cluster[:, 2] == number_of_bedrooms]
    else:
        idealista_cluster = idealista_cluster[idealista_cluster[:, 2] >= number_of_bedrooms]
    if number_of_bathrooms < 3:
        idealista_cluster = idealista_cluster[idealista_cluster[:, 3] == number_of_bathrooms]
    else:
        idealista_cluster = idealista_cluster[idealista_cluster[:, 3] >= number_of_bathrooms]
    """
    idealista_price_max = idealista_price_min[idealista_price_min[:, 4] <= price_max]
    idealista_size_min = idealista_price_max[size_min <= idealista_price_max[:, 5]]
    idealista_size_max = idealista_size_min[idealista_size_min[:, 5] <= size_max]
    if number_of_bedrooms < 4:
        idealista_bedrooms = idealista_size_max[idealista_size_max[:, 2] == number_of_bedrooms]
    else:
        idealista_bedrooms = idealista_size_max[idealista_size_max[:, 2] >= number_of_bedrooms]
    if number_of_bathrooms < 3:
        idealista_bathrooms = idealista_bedrooms[idealista_bedrooms[:, 3] == number_of_bathrooms]
    else:
        idealista_bathrooms = idealista_bedrooms[idealista_bedrooms[:, 3] >= number_of_bathrooms]
    return idealista_bathrooms
    """
    return idealista_cluster


# helper function to process input data
def process_data(submission):
    # reading files
    centroid = pd.read_csv('catalog/data/centroid.csv')
    mean_sd = pd.read_csv('catalog/data/mean_sd.csv')
    cluster_file = open('catalog/data/cluster.txt', 'r')
    clusters = {}
    for c in range(9):
        line = cluster_file.readline()
        clusters[c] = list((map(int, line.rstrip().split(','))))
    # log transformation of certain columns
    cluster_file.close()
    user_input = retrieve_submission(submission)
    cluster, cluster_centroid = rank_distance(user_input, clusters, centroid, mean_sd)
    return cluster, cluster_centroid


def rank_distance(processed_user_input, clusters, centroid, mean_sd):
    # log transformation of certain columns
    user_input = np.array(processed_user_input)
    for col in [3, 6, 7, 9, 10, 11, 15]:
        user_input[col] = np.log(processed_user_input[col])
    # standardize of user_input
    user_input = (np.array(user_input) - mean_sd.iloc[0, :]) / mean_sd.iloc[1, :]
    # calculate distance
    distance = []
    for i in range(9):
        distance.append(np.linalg.norm(user_input - centroid.iloc[i, :].values))
    print('rank distance')
    print(distance)
    return clusters[distance.index(min(distance))], centroid.values[distance.index(min(distance))]


# helper function to retrieve submission value from sliding bar value
def retrieve_submission(submission):
    user_input = []
    questions_dict = {
        'question1': [954.1098000000001, 29793.31],
        'question2': [11.18604, 23.83824],
        'question3_1':[1.661934, 4.889048],
        'question3_2': [0.1424658, 0.9863457],
        'question3_3': [0.3337438, 2.210447],
        'question3_4': [4.455487, 15.06754],
        'question3_5': [0.1316856, 2.367431],
        'question4': [28.76687, 46.03836],
        'question5': [11.32754, 46.34757],
        'question6_1': [7.705809e-05, 0.005723136],
        'question6_2': [0.0001755212, 0.01553212],
        'question6_3': [7.722949e-05, 0.0007817686],
        'question6_4': [0.0003865426, 0.001017774],
        'question6_5': [7.360789e-06, 0.0003245077],
        'question6_6': [0.0001963865, 0.0005479452],
        'question6_7': [0.00133729, 0.003847484],
        'question7': [1.614235, 164.4144]
    }
    question_keys = [
        'question1', 'question2', 'question3_1', 'question3_2', 'question3_3', 'question3_4', 'question3_5',
        'question4', 'question5', 'question6_1', 'question6_2', 'question6_3', 'question6_4', 'question6_5',
        'question6_6', 'question6_7','question7'
    ]
    for question in question_keys:
        if question in submission:
            question_value = int(submission[question][0])
            question_min = questions_dict[question][0]
            question_max = questions_dict[question][1]
            user_input.append(
                (float(question_value) - 1.0) / 999.0 * (question_max - question_min) + question_min
            )
    print('user_input')
    print(user_input)
    return user_input
