from collections.abc import Iterator
from datetime import datetime
import itertools
import json

from bs4 import BeautifulSoup, Tag
import requests

def extract_page_source(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    return None

# Beautiful Soup's built-in `find` and `find_all` methods will not match elements with multiple children when using the
# `string` argument, so we create custom filter lambdas as a workaround
def generate_tag_text_filter(name: str, class_: list[str], text: str):
    return lambda tag: (tag.name == name and
                        set(class_).issubset(set(tag.get('class', []))) and
                        text in tag.get_text())

def to_flat_list_str(l: list) -> str:
    return ', '.join(list(itertools.chain.from_iterable(l)))

# Extracts main stat strings from a div.box element
def extract_main_stats_from_box_div(box_div: Tag) -> str | None:
    return box_div.find('div', class_='list-stats').string

def get_iterator_element_at_index(iterator: Iterator, index: int):
    return next(itertools.islice(iterator, index, None))

def scrape_prydwen(version: str):
    base_url = 'https://www.prydwen.gg'
    characters_url = 'https://www.prydwen.gg/zenless/characters'

    content = extract_page_source(characters_url)

    start_timestamp = datetime.now()

    print(f'{start_timestamp}: Started processing')

    character_url_list = []

    # Extract links to each character's page from main /characters listing
    character_cards = content.find_all('div', class_='avatar-card card')
    if character_cards:
        for character_card in character_cards:
            relative_character_url = character_card.find('a')['href']
            character_url_list.append(f"{base_url}{relative_character_url}")
    else:
        print('Could not find character cards. `/characters` list format must have changed.')

    # # List of test characters. Replace previous block with the commented-out code to extract builds from a limited subset
    # # of agents
    # character_url_list = ['https://www.prydwen.gg/zenless/characters/ellen', # normal agent
    #                       'https://www.prydwen.gg/zenless/characters/astra-yao', # agent with multiple stat builds
    #                       'https://www.prydwen.gg/zenless/characters/evelyn', # agent with missing 2pc set recommendations
    #                       'https://www.prydwen.gg/zenless/characters/aria'] # new agent with no builds

    characters = {}

    for character_url in character_url_list:
        print(f'Now processing: {character_url}')

        character_content = extract_page_source(character_url)

        # Extract character name and element from top section
        character_top_section = character_content.find('div', class_='character-top')
        character_name_element = character_top_section.find('strong')
        character_name = character_name_element.string
        character_element = character_name_element['class'][0]

        characters[character_name] = {
            'Name': character_name
        }

        # Prydwen does not group section headers and their associated sections, so we make liberal use of next_sibling
        drive_discs_header = character_content.find(generate_tag_text_filter(name='div', class_=['content-header', character_element], text='Best Disk Drives Sets'))

        if drive_discs_header:
            drive_discs_section = drive_discs_header.next_sibling

            drive_discs = {}

            four_pc_sections = drive_discs_section.find_all('div', class_=f'single-item {character_element}')
            for i, four_pc_section in enumerate(four_pc_sections):
                four_pc_set_element = four_pc_section.find('span', class_='zzz-weapon-name rarity-S')
                if four_pc_set_element:
                    four_pc_set = next(four_pc_set_element.strings)

                    set_info_section = four_pc_section.next_sibling


                    two_pc_sets_list = set_info_section.find('ul', class_='small-sets')
                    if two_pc_sets_list:
                        two_pc_sets = []
                        recommended_two_pc_sets = []
                        for j, two_pc_sets_section in enumerate(two_pc_sets_list.children):
                            # Each two_pc_sets_section can contain multiple 2pc sets sharing the same 2pc bonus, so
                            # two_pc_sets is an object mapping indexes to lists, where sets in each inner list have the
                            # same 2pc bonus
                            two_pc_set_names = [p.string for p in two_pc_sets_section.find_all('p')]
                            two_pc_sets.append(two_pc_set_names)

                            if '(Recommended)' in two_pc_sets_section.get_text():
                                recommended_two_pc_sets.append(two_pc_set_names)

                        drive_discs[i] = {
                            '4pc Set': four_pc_set,
                            'Recommended 2pc Sets': to_flat_list_str(recommended_two_pc_sets),
                            'All 2pc Sets': to_flat_list_str(two_pc_sets)
                        }
                    elif character_name == 'Evelyn':
                        # As of February 2026, Evelyn only has 4pc sets listed, so we manually populate some 2pc sets
                        # from https://docs.google.com/spreadsheets/d/e/2PACX-1vTj2PaPq6Py_1B5fsOPj_Moc-tN_7mut7fICczI6lz1njyEIAInTnfB7lAraX4pYCRGNbaHGlIbFZ90/pubhtml#gid=0
                        if four_pc_set == 'Hormone Punk':
                            drive_discs[i] = {
                                '4pc Set': four_pc_set,
                                'Recommended 2pc Sets': 'Puffer Electro',
                                'All 2pc Sets': 'Puffer Electro, Branch & Blade Song, Woodpecker Electro, Astral Voice, Inferno Metal'
                            }
                        elif four_pc_set == 'Puffer Electro':
                            drive_discs[i] = {
                                '4pc Set': four_pc_set,
                                'Recommended 2pc Sets': 'Branch & Blade Song, Woodpecker Electro',
                                'All 2pc Sets': 'Branch & Blade Song, Woodpecker Electro, Astral Voice, Hormone Punk, Inferno Metal'
                            }
                        elif four_pc_set == 'Astral Voice':
                            drive_discs[i] = {
                                '4pc Set': four_pc_set,
                                'Recommended 2pc Sets': 'Puffer Electro',
                                'All 2pc Sets': 'Puffer Electro, Branch & Blade Song, Woodpecker Electro, Hormone Punk, Inferno Metal'
                            }
                    else:
                        print('Could not find 2pc sets')
                else:
                    print('Could not find 4pc set name')

            characters[character_name]['Drive Discs'] = drive_discs

            stats_header = character_content.find(generate_tag_text_filter(name='div', class_=['content-header', character_element], text='Best Disk Drives Stats'))
            if stats_header:
                stats_section = stats_header.next_sibling

                disc_four_stats = []
                disc_five_stats = []
                disc_six_stats = []
                substats = []

                # Some characters like Astra have multiple `.main-stats` sections corresponding to different builds, so
                # we represent each stat as a list and join the values for each stat
                main_stats_sections = stats_section.find_all('div', class_='main-stats')
                for main_stats_section in main_stats_sections:
                    disc_four_stats.append(extract_main_stats_from_box_div(main_stats_section.contents[0]))
                    disc_five_stats.append(extract_main_stats_from_box_div(main_stats_section.contents[1]))
                    disc_six_stats.append(extract_main_stats_from_box_div(main_stats_section.contents[2]))

                    substats_section = main_stats_section.next_sibling
                    substats.append(get_iterator_element_at_index(substats_section.find('p').strings, 2))

                # Dedupe any repeated values for clarity
                disc_four_stats = list(dict.fromkeys(disc_four_stats))
                disc_five_stats = list(dict.fromkeys(disc_five_stats))
                disc_six_stats = list(dict.fromkeys(disc_six_stats))
                substats = list(dict.fromkeys(substats))

                characters[character_name]['Stats'] = {
                    'Disc 4': ', '.join(disc_four_stats),
                    'Disc 5': ', '.join(disc_five_stats),
                    'Disc 6': ', '.join(disc_six_stats),
                    'Substats': ', '.join(substats)
                }

            else:
                print('Could not find Stats section')
        else:
            print('Could not find Drive Discs section')

        print(f'Finished processing: {character_url}')

    file_path = f"characters_output_{version}.json"

    with open(file_path, 'w') as json_file:
        json.dump(characters, json_file)

    print(f"The dictionary has been saved to {file_path}.")

    end_timestamp = datetime.now()
    print(f"{end_timestamp}: Completed processing")
    print(f"Took: {(end_timestamp - start_timestamp).total_seconds() % 60}")