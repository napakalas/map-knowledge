import pytest
from mapknowledge import KnowledgeStore

store = KnowledgeStore(sckan_version='sckan-2024-09-21')

def test_path_contains_expected_nerves():
    knowledge = store.entity_knowledge('ilxtr:neuron-type-keast-8')
    nerves = set(knowledge.get('nerves', []))
    expected_nerves = {('ILX:0793221', ()), ('ILX:0793220', ())}
    
    assert expected_nerves.issubset(nerves)
    assert len(nerves) == 2

def test_known_nerve_type():
    knowledge = store.entity_knowledge('ILX:0793221')
    assert knowledge.get('type') == 'nerve'

def test_non_nerve_type():
    knowledge = store.entity_knowledge('UBERON:0006448')
    assert knowledge.get('type') != 'nerve'

store.close()
