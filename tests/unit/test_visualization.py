import base64
import json

import pytest

from woodblock.visualization import build_view_model, create_visualization, render_html


def _metadata():
    """A small but representative ground-truth metadata document.

    Two real files split across two scenarios, plus a filler fragment, laid out so that the
    fragments interleave in the image and one padding gap is present.
    """
    return {
        'block_size': 512,
        'seed': 4711,
        'corpus': '/corpus',
        'scenarios': [
            {
                'name': 'first',
                'files': [
                    {
                        'original': {'type': 'file', 'sha256': 'a' * 64, 'size': 1024, 'path': 'a.bin', 'id': 'fa'},
                        'fragments': [
                            {
                                'sha256': 'a1' * 32,
                                'size': 512,
                                'number': 1,
                                'file_offsets': {'start': 0, 'end': 512},
                                'image_offsets': {'start': 0, 'end': 512},
                            },
                            {
                                'sha256': 'a2' * 32,
                                'size': 512,
                                'number': 2,
                                'file_offsets': {'start': 512, 'end': 1024},
                                'image_offsets': {'start': 1024, 'end': 1536},
                            },
                        ],
                    },
                    {
                        'original': {'type': 'file', 'sha256': 'b' * 64, 'size': 512, 'path': 'b.bin', 'id': 'fb'},
                        'fragments': [
                            {
                                'sha256': 'b1' * 32,
                                'size': 512,
                                'number': 1,
                                'file_offsets': {'start': 0, 'end': 512},
                                'image_offsets': {'start': 512, 'end': 1024},
                            }
                        ],
                    },
                ],
            },
            {
                'name': 'second',
                'files': [
                    {
                        'original': {'type': 'filler', 'sha256': 'c' * 64, 'size': 300, 'path': 'random', 'id': 'fc'},
                        'fragments': [
                            {
                                'sha256': 'c1' * 32,
                                'size': 300,
                                'number': 1,
                                'file_offsets': {'start': 0, 'end': 300},
                                'image_offsets': {'start': 1536, 'end': 1836},
                            }
                        ],
                    }
                ],
            },
        ],
    }


class TestBuildViewModel:
    def test_image_wide_settings_are_carried_over(self):
        vm = build_view_model(_metadata())
        assert vm['block_size'] == 512
        assert vm['seed'] == 4711
        assert vm['corpus'] == '/corpus'

    def test_image_size_is_rounded_up_to_the_block_boundary(self):
        # last fragment ends at 1836, so the image is padded up to 2048 (4 * 512).
        assert build_view_model(_metadata())['image_size'] == 2048

    def test_real_files_get_distinct_color_indices_and_fillers_get_none(self):
        files = {f['id']: f for f in build_view_model(_metadata())['files']}
        assert files['fa']['color_index'] == 0
        assert files['fb']['color_index'] == 1
        assert files['fc']['color_index'] is None
        assert files['fc']['type'] == 'filler'

    def test_only_real_files_are_counted(self):
        vm = build_view_model(_metadata())
        assert vm['num_files'] == 2
        assert vm['num_fragments'] == 4
        assert len(vm['files']) == 3  # two files + one filler

    def test_fragments_are_sorted_by_image_offset(self):
        starts = [f['image_start'] for f in build_view_model(_metadata())['fragments']]
        assert starts == sorted(starts)
        assert starts == [0, 512, 1024, 1536]

    def test_segments_interleave_fragments_with_padding(self):
        segments = build_view_model(_metadata())['segments']
        # the filler ends at 1836; the trailing padding region fills up to the image size.
        assert segments[-1] == {'kind': 'padding', 'image_start': 1836, 'image_end': 2048}
        kinds = [s['kind'] for s in segments]
        assert kinds.count('fragment') == 4

    def test_fragments_keep_their_owning_file_color(self):
        frags = {(f['file_id'], f['number']): f for f in build_view_model(_metadata())['fragments']}
        assert frags[('fa', 1)]['color_index'] == 0
        assert frags[('fa', 2)]['color_index'] == 0

    def test_fragments_get_config_style_layout_labels(self):
        # N.M for corpus files (N = per-scenario file index, M = fragment number); R/Z for fillers.
        frags = {(f['file_id'], f['number']): f for f in build_view_model(_metadata())['fragments']}
        assert frags[('fa', 1)]['label'] == '1.1'
        assert frags[('fa', 2)]['label'] == '1.2'
        assert frags[('fb', 1)]['label'] == '2.1'
        assert frags[('fc', 1)]['label'] == 'R'  # the filler's path is "random"

    def test_real_files_are_numbered_per_scenario(self):
        files = {f['id']: f for f in build_view_model(_metadata())['files']}
        assert files['fa']['scenario_file_number'] == 1
        assert files['fb']['scenario_file_number'] == 2
        assert files['fc']['scenario_file_number'] is None  # fillers are not numbered


class TestRenderHtml:
    def test_all_template_markers_are_substituted(self):
        html = render_html(_metadata())
        for marker in ('__TITLE__', '__VIEW_MODEL_JSON__', '__IMAGE_BASE64__', '__HAS_EMBEDDED__'):
            assert marker not in html

    def test_view_model_is_embedded_and_parseable(self):
        html = render_html(_metadata())
        start = html.index('id="view-model">') + len('id="view-model">')
        end = html.index('</script>', start)
        vm = json.loads(html[start:end].replace('\\u003c', '<'))
        assert vm['num_files'] == 2

    def test_angle_brackets_in_data_are_escaped_for_safe_embedding(self):
        meta = _metadata()
        meta['scenarios'][0]['files'][0]['original']['path'] = 'evil</script>.bin'
        html = render_html(meta)
        assert '</script>.bin' not in html
        assert '\\u003c/script>.bin' in html

    def test_without_image_bytes_the_viewer_is_not_embedded(self):
        html = render_html(_metadata())
        assert 'const HAS_EMBEDDED = false' in html

    def test_uses_the_scrollable_hex_viewer_and_map_viewport(self):
        html = render_html(_metadata())
        assert 'id="viewport"' in html
        assert 'id="hex-scroll"' in html
        # the hex view carries a right-hand file-indicator gutter
        assert 'id="hex-gutter"' in html
        # the old one-fragment-at-a-time paging controls are gone
        assert 'id="prev"' not in html
        assert 'id="next"' not in html

    def test_image_bytes_are_embedded_as_base64(self):
        payload = b'hello woodblock'
        html = render_html(_metadata(), image_bytes=payload)
        assert 'const HAS_EMBEDDED = true' in html
        start = html.index('id="image-data">') + len('id="image-data">')
        end = html.index('</script>', start)
        assert base64.b64decode(html[start:end].strip()) == payload


class TestCreateVisualization:
    def test_writes_html_next_to_the_image(self, tmp_path):
        meta_path = tmp_path / 'img.dd.json'
        meta_path.write_text(json.dumps(_metadata()))
        image_path = tmp_path / 'img.dd'
        image_path.write_bytes(b'\x00' * 2048)

        out = create_visualization(meta_path, image=image_path)

        assert out == tmp_path / 'img.dd.html'
        assert out.is_file()
        assert 'const HAS_EMBEDDED = true' in out.read_text()

    def test_derives_output_from_metadata_when_no_image_is_given(self, tmp_path):
        meta_path = tmp_path / 'img.dd.json'
        meta_path.write_text(json.dumps(_metadata()))

        out = create_visualization(meta_path)

        assert out == tmp_path / 'img.dd.html'
        assert 'const HAS_EMBEDDED = false' in out.read_text()

    def test_large_images_are_not_embedded(self, tmp_path):
        meta_path = tmp_path / 'img.dd.json'
        meta_path.write_text(json.dumps(_metadata()))
        image_path = tmp_path / 'img.dd'
        image_path.write_bytes(b'\x00' * 4096)

        out = create_visualization(meta_path, image=image_path, max_embed_bytes=1024)

        assert 'const HAS_EMBEDDED = false' in out.read_text()

    def test_accepts_a_metadata_dict_directly(self, tmp_path):
        out = create_visualization(_metadata(), output=tmp_path / 'viz.html')
        assert out.is_file()

    def test_requires_an_output_when_given_a_dict_without_paths(self):
        with pytest.raises(ValueError):
            create_visualization(_metadata())
