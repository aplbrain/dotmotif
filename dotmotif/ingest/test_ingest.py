import unittest
import pandas as pd
from . import EdgelistConverter
import io


class TestEdgelistIngest(unittest.TestCase):
    def test_ingest(self):
        df = pd.DataFrame(
            [
                {
                    "source": "A",
                    "target": "B",
                },
                {
                    "source": "A",
                    "target": "C",
                },
            ]
        )
        converter = EdgelistConverter(df, "source", "target")
        graph = converter.to_graph()
        self.assertEqual(graph.number_of_nodes(), 3)

    def test_read_csv(self):
        converter = EdgelistConverter(
            io.StringIO("source,target\n" "A,B\n" "A,C\n"),
            "source",
            "target",
        )
        graph = converter.to_graph()
        self.assertEqual(graph.number_of_nodes(), 3)

    def test_fails_on_invalid_columns(self):
        with self.assertRaises(KeyError):
            EdgelistConverter(
                pd.DataFrame(
                    [{"source": "A", "target": "B"}],
                ),
                "source",
                "MISSING_COLUMN_NAME",
            )
        with self.assertRaises(KeyError):
            EdgelistConverter(
                pd.DataFrame(
                    [{"source": "A", "target": "B"}],
                ),
                "MISSING_COLUMN_NAME",
                "source",
            )

    def test_stringifies_integers_as_long(self):
        df = pd.DataFrame(
            [
                {"source": 648518346349539500, "target": 648518346349539500 + 1},
                {"source": 648518346349539500, "target": 648518346349539500 + 2},
            ]
        )
        converter = EdgelistConverter(df, "source", "target")
        graph = converter.to_graph()
        self.assertEqual(graph.number_of_nodes(), 3)
