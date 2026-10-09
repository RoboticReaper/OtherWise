"""Acceptance must fail when sampled claims, edges or current versions are unchecked."""
import copy
import unittest

from audit_gate import assess


class AuditGateTests(unittest.TestCase):
    def setUp(self):
        self.cards = []
        self.entries = []
        self.reviews = []
        for n in range(40):
            cid = f'Q{n+1}'
            card = {'id': cid, 'card_version': 1, 'card': 'A supported explanation.', 'relations': []}
            stratum = 'random' if n < 20 else 'risk'
            self.cards.append(card)
            self.entries.append({'id': cid, 'stratum': stratum, 'card': copy.deepcopy(card)})
            self.reviews.append({'id': cid, 'stratum': stratum, 'card_version': 1, 'status': 'verified',
                'claims': [{'url': 'https://example.org/source', 'locator': 'Definition',
                    'inspection_mode': 'text inspection', 'supported': True}],
                'clarity': {'meaning_clear': True, 'concrete_takeaway': True,
                    'qualification_preserved': True, 'scope_appropriate_wording': True},
                'relations': [], 'findings': []})
        self.sample = {'draft_candidate_sha256': 'a'*64, 'sample': self.entries}
        self.initial = [{'authored_sampled_cards': False, 'draft_candidate_sha256': 'a'*64,
                         'reviews': self.reviews}]

    def assess(self, rechecks=None):
        return assess(self.sample, self.cards, self.initial, rechecks or [])

    def test_complete_verified_unchanged_sample_passes(self):
        self.assertEqual(self.assess()['status'], 'passed')

    def test_missing_random_review_blocks_acceptance(self):
        self.reviews.pop(0)
        self.assertEqual(self.assess()['status'], 'failed')

    def test_omitted_attached_relationship_blocks_acceptance(self):
        edge = {'target_id': 'Q99', 'type': 'broader_topic', 'assertion': 'editorial'}
        self.cards[0]['relations'] = [edge]
        self.entries[0]['card']['relations'] = [edge]
        self.assertEqual(self.assess()['status'], 'failed')

    def test_changed_sample_text_requires_fresh_recheck(self):
        self.cards[0]['card'] = 'Changed claim with no inspection.'
        self.assertEqual(self.assess()['status'], 'failed')

    def test_repair_with_wrong_current_hash_cannot_pass(self):
        self.cards[0]['card_version'] = 2
        review = copy.deepcopy(self.reviews[0])
        review.update(card_version=2, current_card_sha256='b'*64)
        recheck = {'authored_sampled_cards': False, 'reviews': [review],
                   'current_input_sha256': {'candidate.json': 'c'*64}}
        self.assertEqual(self.assess([recheck])['status'], 'failed')

    def test_uninspected_claim_cannot_pass_despite_verified_flag(self):
        self.reviews[0]['claims'][0]['inspection_mode'] = ''
        self.assertEqual(self.assess()['status'], 'failed')


if __name__ == '__main__': unittest.main()
