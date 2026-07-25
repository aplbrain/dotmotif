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
            io.StringIO("source,target\nA,B\nA,C\n"),
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

    def test_endpoint_dtypes_apply_to_dataframes(self):
        converter = EdgelistConverter(
            pd.DataFrame([{"source": "1", "target": "2"}]),
            "source",
            "target",
            u_id_column_dtype=int,
            v_id_column_dtype=float,
        )

        self.assertEqual(set(converter.to_graph().nodes), {1, 2.0})

    def test_endpoint_dtypes_apply_while_reading_files(self):
        converter = EdgelistConverter(
            io.StringIO("source,target\n1,2\n"),
            "source",
            "target",
            u_id_column_dtype=int,
            v_id_column_dtype=int,
        )

        self.assertEqual(set(converter.to_graph().nodes), {1, 2})

    def test_extension_dtypes_are_supported(self):
        converter = EdgelistConverter(
            io.StringIO("source,target\n1,2\n"),
            "source",
            "target",
            u_id_column_dtype=pd.Int64Dtype(),
            v_id_column_dtype=pd.Int64Dtype(),
        )

        self.assertEqual(set(converter.to_graph().nodes), {1, 2})

    def test_boolean_dtypes_parse_strings_consistently(self):
        dataframe = pd.DataFrame([{"source": "False", "target": "True"}])
        from_dataframe = EdgelistConverter(
            dataframe,
            "source",
            "target",
            u_id_column_dtype=bool,
            v_id_column_dtype=bool,
        ).to_graph()
        from_file = EdgelistConverter(
            io.StringIO("source,target\nFalse,True\n"),
            "source",
            "target",
            u_id_column_dtype=bool,
            v_id_column_dtype=bool,
        ).to_graph()

        self.assertEqual(set(from_dataframe.nodes), {False, True})
        self.assertEqual(set(from_file.nodes), {False, True})

    def test_missing_endpoint_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot contain missing values"):
            EdgelistConverter(
                pd.DataFrame([{"source": 1, "target": None}]),
                "source",
                "target",
                u_id_column_dtype=pd.Int64Dtype(),
                v_id_column_dtype=pd.Int64Dtype(),
            )
        with self.assertRaisesRegex(ValueError, "cannot contain missing values"):
            EdgelistConverter(
                pd.DataFrame([{"source": "A", "target": None}]),
                "source",
                "target",
            )
