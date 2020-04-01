import json
import requests
import streamlit as st
from pymongo import MongoClient

import SessionState
from utils import load_dataset, save_dataset, format_txt


DATASET_PATH = 'fr/uniform_sampling'

# Connect to local Mongo DB
products = MongoClient(
    host='localhost',
    port=27017,
).off.products


def display_image(item_id):
    # Display ingredients image based on OFF API
    try:
        url = f'https://world.openfoodfacts.org/api/v0/product/{item_id}.json'
        data = requests.get(url).json()
        image_url = data['product']['selected_images']['ingredients']['display'].get('fr')
        st.image(image_url)
    except Exception as e:
        st.error(f'No image found for item {item_id}')
        st.error(e)


def save_corrected_item(item, correct):
    session.corrected_items.append({
        '_id': item['_id'],
        'original': item['ingredients_text_fr'],
        'correct': correct,
    })
    save_dataset('fr/uniform_sampling', session.corrected_items)


@st.cache(allow_output_mutation=True)
def query_items(limit):
    query = products.aggregate([
        {'$match': {'ingredients_text_fr': {'$exists': True, '$ne': ''}}},
        {'$sample': {'size': limit}},
        {'$project': {'ingredients_text_fr': 1}},
    ])
    # Flatten generator for caching issues
    return [item for item in query]


session = SessionState.get(
    cursor=0,
    corrected_items=load_dataset(DATASET_PATH),
)

# Select an item to label/correct
items_to_label = query_items(limit=10000)
while True:
    try:
        item = items_to_label[session.cursor]
        item['ingredients_text_fr'] = format_txt(item['ingredients_text_fr'])
    except IndexError:
        st.error('No more cached items. Need to rerun Streamlit CLI once.')
        break
    if item['_id'] not in [corrected_item['_id'] for corrected_item in session.corrected_items]:
        break
    session.cursor += 1


# Interface
st.title('OFF spellcheck label tool')
st.info(f'{len(session.corrected_items)} items have been labelled ! Keep going ! :)')
st.subheader(f'Item id : {item["_id"]}')
st.subheader('Raw text')
st.write(f'```{item["ingredients_text_fr"]}```')
st.subheader('Correction')
correct = st.text_area('Type corrected text here', value=item['ingredients_text_fr'])
display_image(item['_id'])

if st.button('Submit'):
    save_corrected_item(item, correct)
    SessionState.rerun()

elif st.button('Too noisy'):
    save_corrected_item(item, 'NOT_VALID__TOO_NOISY')
    SessionState.rerun()

elif st.button('Incomplete'):
    save_corrected_item(item, 'NOT_VALID__INCOMPLETE')
    SessionState.rerun()

elif st.button('Not ingredients'):
    save_corrected_item(item, 'NOT_VALID__NOT_INGREDIENTS')
    SessionState.rerun()

elif st.button('Not expected language'):
    save_corrected_item(item, 'NOT_VALID__NOT_LANGUAGE')
    SessionState.rerun()

elif st.button('Other'):
    save_corrected_item(item, 'NOT_VALID__OTHER')
    SessionState.rerun()