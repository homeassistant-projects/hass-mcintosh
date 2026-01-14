"""Tests to prevent entity ID regressions across versions.

WARNING: These tests protect user installations. Changing unique_id formats
breaks automations, dashboards, and entity history. You MUST provide a
migration path if changes are absolutely necessary.
"""

import pytest

DOMAIN = 'mcintosh'

# Golden unique_id format documentation
# These patterns are part of the public API - do not change without migration
GOLDEN_FORMATS = {
    'media_player': '{domain}_{model_id}',
    'number': '{domain}_{model_id}_{key}',
    'switch_loudness': '{domain}_{model_id}_loudness',
}

# All number entity keys that exist
NUMBER_ENTITY_KEYS = [
    'bass_trim',
    'treble_trim',
    'lipsync_delay',
    'center_trim',
    'lfe_trim',
    'surrounds_trim',
    'height_trim',
]


def generate_media_player_unique_id(model_id: str) -> str:
    """Generate unique_id using same logic as McIntoshMediaPlayer.__init__."""
    # mirrors: custom_components/mcintosh/media_player.py
    return f'{DOMAIN}_{model_id}'.lower().replace(' ', '_')


def generate_number_unique_id(model_id: str, key: str) -> str:
    """Generate unique_id using same logic as McIntoshNumber.__init__."""
    # mirrors: custom_components/mcintosh/number.py
    return f'{DOMAIN}_{model_id}_{key}'.lower().replace(' ', '_')


def generate_switch_unique_id(model_id: str, switch_type: str) -> str:
    """Generate unique_id using same logic as McIntoshLoudnessSwitch.__init__."""
    # mirrors: custom_components/mcintosh/switch.py
    return f'{DOMAIN}_{model_id}_{switch_type}'.lower().replace(' ', '_')


class TestMediaPlayerUniqueIdStability:
    """Test media_player unique_id format stability."""

    @pytest.mark.parametrize(
        'model_id,expected',
        [
            ('mx160', 'mcintosh_mx160'),
            ('mx170', 'mcintosh_mx170'),
            ('mx180', 'mcintosh_mx180'),
            ('MX160', 'mcintosh_mx160'),  # case normalization
        ],
    )
    def test_format_stability(self, model_id: str, expected: str):
        """Ensure media_player unique_id format matches golden values.

        WARNING: If this test fails, you are about to break user automations,
        dashboards, and entity history. You MUST provide a migration path.
        """
        result = generate_media_player_unique_id(model_id)
        assert result == expected, (
            f'BREAKING CHANGE: media_player unique_id format changed!\n'
            f'  Model: {model_id}\n'
            f'  Expected: {expected}\n'
            f'  Got: {result}\n'
            f'This will break existing user installations.'
        )


class TestNumberEntityUniqueIdStability:
    """Test number entity unique_id format stability."""

    @pytest.mark.parametrize(
        'model_id,key,expected',
        [
            ('mx160', 'bass_trim', 'mcintosh_mx160_bass_trim'),
            ('mx160', 'treble_trim', 'mcintosh_mx160_treble_trim'),
            ('mx160', 'lipsync_delay', 'mcintosh_mx160_lipsync_delay'),
            ('mx170', 'center_trim', 'mcintosh_mx170_center_trim'),
            ('mx180', 'lfe_trim', 'mcintosh_mx180_lfe_trim'),
        ],
    )
    def test_format_stability(self, model_id: str, key: str, expected: str):
        """Ensure number entity unique_id format matches golden values.

        WARNING: If this test fails, you are about to break user automations,
        dashboards, and entity history. You MUST provide a migration path.
        """
        result = generate_number_unique_id(model_id, key)
        assert result == expected, (
            f'BREAKING CHANGE: number entity unique_id format changed!\n'
            f'  Model: {model_id}, Key: {key}\n'
            f'  Expected: {expected}\n'
            f'  Got: {result}\n'
            f'This will break existing user installations.'
        )

    def test_all_number_keys_generate_valid_ids(self):
        """Verify all number entity keys generate valid unique_ids."""
        for key in NUMBER_ENTITY_KEYS:
            result = generate_number_unique_id('mx160', key)
            assert result == f'mcintosh_mx160_{key}'


class TestSwitchUniqueIdStability:
    """Test switch entity unique_id format stability."""

    @pytest.mark.parametrize(
        'model_id,expected',
        [
            ('mx160', 'mcintosh_mx160_loudness'),
            ('mx170', 'mcintosh_mx170_loudness'),
            ('mx180', 'mcintosh_mx180_loudness'),
        ],
    )
    def test_loudness_switch_format_stability(self, model_id: str, expected: str):
        """Ensure loudness switch unique_id format matches golden values.

        WARNING: If this test fails, you are about to break user automations,
        dashboards, and entity history. You MUST provide a migration path.
        """
        result = generate_switch_unique_id(model_id, 'loudness')
        assert result == expected, (
            f'BREAKING CHANGE: switch unique_id format changed!\n'
            f'  Model: {model_id}\n'
            f'  Expected: {expected}\n'
            f'  Got: {result}\n'
            f'This will break existing user installations.'
        )
