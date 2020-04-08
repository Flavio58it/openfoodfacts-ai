
import sys
from statistics import mean
from difflib import SequenceMatcher
from ingredients import process_ingredients


# TODO : refacto this scripts as a proper Evaluation class

def evaluation_metrics(items, prediction_txts):
    output = {}

    txt_metrics = per_items_list_txt_metrics(items, prediction_txts)
    output.update(txt_metrics)

    ingredients_metrics = dict_list_mean([
        per_item_ingredients_metrics(item, prediction_txt)
        for item, prediction_txt in zip(items, prediction_txts)
    ])
    output.update(ingredients_metrics)

    similarity_metric = mean([
        per_item_similarity_based_metric(item, prediction_txt)
        for item, prediction_txt in zip(items, prediction_txts)
    ])
    output['txt_similarity_metric'] = similarity_metric

    return output


def per_items_list_txt_metrics(items, prediction_txts):
    """
    Precision :
        number of times we have the correct answer when we changed something
                / number of times we changed something

    Recall :
        number of times we have the correct answer when we changed something
                / number of times we should have changed something
    """
    number_correct_answers_when_changes = 0
    number_changed = 0
    number_should_have_been_changed = 0

    for item, prediction_txt in zip(items, prediction_txts):
        if item['original'] != prediction_txt:
            number_changed += 1
            if item['correct'] == prediction_txt:
                number_correct_answers_when_changes += 1
        if item['original'] != item['correct']:
            number_should_have_been_changed += 1

    return {
        'number_items': len(items),
        'number_changed': number_changed,
        'number_should_have_been_changed': number_should_have_been_changed,
        'txt_precision': ratio(number_correct_answers_when_changes, number_changed),
        'txt_recall': ratio(number_correct_answers_when_changes, number_should_have_been_changed),
    }


def per_item_ingredients_metrics(item, prediction_txt, remove_originals=False):
    """
    Precision :
        number of times we have predicted a correct ingredient
            / number of predicted ingredients

    Recall :
        number of times we have predicted a correct ingredient
            / number of correct ingredients
    """
    original_ingredients = format_ingredients(item['original'])
    correct_ingredients = format_ingredients(item['correct'])
    predicted_ingredients = format_ingredients(prediction_txt)

    original_correct_predicted_ingredients = original_ingredients & correct_ingredients & predicted_ingredients
    original_correct_ingredients = original_ingredients & correct_ingredients
    correct_predicted_ingredients = correct_ingredients & predicted_ingredients

    return {
        'ingr_precision': ratio(
            correct_predicted_ingredients,
            predicted_ingredients
        ),
        'ingr_precision_on_errors': ratio(
            correct_predicted_ingredients - original_correct_predicted_ingredients,
            predicted_ingredients - original_correct_predicted_ingredients
        ),
        'ingr_recall': ratio(
            correct_predicted_ingredients,
            correct_ingredients,
        ),
        'ingr_recall_on_errors': ratio(
            correct_predicted_ingredients-original_correct_predicted_ingredients,
            correct_ingredients-original_correct_predicted_ingredients,
        ),
        'ingr_fidelity': ratio(
            original_correct_predicted_ingredients,
            original_correct_ingredients,
        ),
    }


def ratio(numerator, denominator):
    if isinstance(numerator, set):
        numerator = len(numerator)
    if isinstance(denominator, set):
        denominator = len(denominator)
    if denominator == 0:
        return
    return 100.0 * numerator / denominator


def dict_list_mean(dict_list):
    assert(len(dict_list) > 0)
    first_item = dict_list[0]
    output = {}
    for key in first_item.keys():
        output[key] = mean([item[key] for item in dict_list if item[key] is not None])
    return output


def format_ingredients(ingredients_txt):
    return {
        ' '.join(ingredient.split())
        for ingredient
        in process_ingredients(ingredients_txt).iter_normalized_ingredients()
    }


def per_item_similarity_based_metric(item, prediction_txt):
    matcher = SequenceMatcher(is_junk, item['correct'], prediction_txt)
    return 100.0 * matcher.ratio()


def is_junk(c):
    return False
