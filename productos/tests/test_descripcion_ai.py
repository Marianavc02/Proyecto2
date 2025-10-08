# productos/tests/test_descripcion_ai.py
from unittest.mock import patch

import pytest

from SBDToolBox.ia.descriptions import generate_product_blurb


@pytest.mark.django_db
class TestDescripcionAI:

    @patch("SBDToolBox.ia.descriptions._has_key", return_value=True)
    @patch("SBDToolBox.ia.descriptions.requests.post")
    def test_genera_descripcion_si_no_hay_original(self, mock_post, _):
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Martillo Stanley de acero forjado, resistente y ergonómico."}}]
        }
        mock_post.return_value.raise_for_status = lambda: None

        descripcion = generate_product_blurb(
            nombre="Martillo Stanley", sku="SKU123", empresa="Stanley", categoria="Herramientas"
        )

        assert descripcion is not None
        assert "Martillo Stanley" in descripcion

    @patch("SBDToolBox.ia.descriptions._has_key", return_value=False)
    def test_no_genera_si_no_hay_api_key(self, _):
        descripcion = generate_product_blurb(nombre="Martillo", sku="SKU456", empresa="Stanley", categoria="Ferretería")
        assert descripcion is None

    @patch("SBDToolBox.ia.descriptions._has_key", return_value=True)
    @patch("SBDToolBox.ia.descriptions.requests.post", side_effect=Exception("Falla conexión"))
    def test_no_falla_si_la_api_falla(self, _, __):
        descripcion = generate_product_blurb(
            nombre="Destornillador", sku="SKU789", empresa="Stanley", categoria="Herramientas"
        )
        assert descripcion is None

    @patch("SBDToolBox.ia.descriptions._has_key", return_value=True)
    @patch("SBDToolBox.ia.descriptions.requests.post")
    def test_limpieza_y_recorte(self, mock_post, _):
        contenido_largo = " ".join(["Palabra"] * 200)
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": contenido_largo}}]}
        mock_post.return_value.raise_for_status = lambda: None
    
        descripcion = generate_product_blurb(nombre="Taladro", sku="SKU000", empresa="DeWalt", categoria="Construcción")
    
        assert len(descripcion) <= 600  # nosec B101
        assert "  " not in descripcion  # nosec B101
    

