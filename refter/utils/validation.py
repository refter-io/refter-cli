import sys
from typing import Dict, List, Mapping, Optional, Tuple, cast

from dbt.contracts.graph.manifest import WritableManifest
from dbt.contracts.graph.nodes import ManifestNode, ModelNode
from pydantic import ValidationError
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

from refter.constants import CONFIG_KEY
from refter.types import ColumnConfig, TableConfig, ValidateError


def _get_ref_schema_and_table(ref: str) -> Tuple[Optional[str], str]:
    """
    Helper to get schema and table from a reference
    """
    if "." not in ref:
        return None, ref

    components = ref.split(".")

    if len(components) > 2:
        raise ValueError(f"Invalid reference: {ref}")

    return components[0], components[1]


def _find_model_for_schema_and_table(
    schema: Optional[str], table: str, nodes: List[ManifestNode]
) -> Optional[ModelNode]:  # type: ignore
    """
    Helper to find a model node for a given schema and table
    """
    for node in nodes:
        node_name = node.alias or node.name
        node_schema: Optional[str] = node.config.schema or node.schema
        if not schema:
            node_schema = None

        if node_schema == schema and node_name == table:
            return node  # type: ignore

    return None


def _find_nodes_with_references(
    nodes: List[ManifestNode],
) -> List[ManifestNode]:
    """
    Helper to find nodes that have columns with "refers_to" references
    """
    nodes_with_refs = list(
        filter(
            lambda node: any(CONFIG_KEY in col._extra for col in node.columns.values()),
            nodes,
        )
    )
    return nodes_with_refs


def _validate_references(
    manifest: WritableManifest,
) -> Mapping[str, List[ValidateError]]:
    nodes = cast(List[ManifestNode], manifest.nodes.values())
    nodes_with_refs = list(
        filter(
            lambda node: node.config.get(CONFIG_KEY) is not None,
            nodes,
        )
    )

    errors: Dict[str, List[ValidateError]] = {}

    for node in nodes_with_refs:
        schema = node.config.schema or node.schema
        table = node.alias or node.name
        node_name = f"{schema}.{table}"

        table_config = node.config.get(CONFIG_KEY, {})
        if not table_config:
            continue

        try:
            TableConfig.validate(table_config)
        except ValidationError as exc:
            errors[node_name] = [
                ValidateError(
                    field=".".join(err.get("loc")),  # type: ignore
                    message=err.get("msg", "Unknown error"),
                    type=err.get("type", "unknown"),
                )  # type: ignore
                for err in exc.errors()
            ]

    return errors


def _validate_column_references(
    manifest: WritableManifest,
) -> Mapping[str, List[ValidateError]]:
    """
    Validate that all references in the manifest are valid.
    1. Check that column refers_to has valid configuration
    2. Check that column refers_to references a valid model
    3. Check that column refers_to references a valid column

    Returns
    -------
    Mapping[str, List[str]]
        A mapping of node name to a list of errors for that node
    """
    errors: Dict[str, List[ValidateError]] = {}
    nodes = cast(List[ManifestNode], manifest.nodes.values())
    refable_nodes = list(filter(lambda node: node.is_refable, nodes))
    nodes_with_refs = _find_nodes_with_references(refable_nodes)

    for node in nodes_with_refs:
        schema = node.config.schema or node.schema
        table = node.alias or node.name
        node_name = f"{schema}.{table}"

        errors[node_name] = []
        columns = node.columns.values()
        for column in columns:
            column_config = column._extra.get(CONFIG_KEY, {})

            try:
                ColumnConfig.validate(column_config)
            except ValidationError as exc:
                node_errors = [
                    ValidateError(
                        column=column.name,
                        field=".".join(
                            ([str(x) for x in err.get("loc", [])])
                        ),  # type: ignore
                        message=err.get("msg", "Unknown error"),
                        type=err.get("type", "unknown"),
                    )
                    for err in exc.errors()
                ]
                errors[node_name].extend(node_errors)
                continue

            relations = column_config.get("relations", [])
            for ref in relations:
                # Check if refers_to references a valid dbt node
                ref_schema, ref_table = _get_ref_schema_and_table(ref["model"])
                ref_model = _find_model_for_schema_and_table(
                    ref_schema, ref_table, refable_nodes
                )

                if not ref_model:
                    errors[node_name].append(
                        ValidateError(
                            column=column.name,
                            field="model",
                            message=f"{ref['model']} does not exist."
                            + " Try referencing it using the schema.table"
                            + " syntax or using it's alias.",
                            type="model_not_found",
                        )
                    )
                    continue

                if ref["column"] not in ref_model.columns.keys():
                    errors[node_name].append(
                        ValidateError(
                            column=column.name,
                            field="column",
                            message=f"{ref['column']} does"
                            + f" not exist in {ref['model']}",
                            type="column_not_found",
                        )
                    )

    return {k: v for k, v in errors.items() if v}


def _print_validation_errors(
    table_errors: Mapping[str, List[ValidateError]],
    column_errors: Mapping[str, List[ValidateError]],
) -> None:
    """
    Helper to report on validation errors
    """
    console = Console()

    console.print(
        Padding(
            f"{len(table_errors.keys())} model configuration errors:",
            (1, 0),
            style="bold dim cyan",
        )
    )
    for node_name, node_errors in table_errors.items():
        table = Table(
            title=node_name,
            title_justify="left",
            title_style="bold red",
            show_lines=True,
        )
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Message", style="magenta")
        table.add_column("Type", style="red")

        for err in node_errors:
            table.add_row(err.field, err.message, err.type)

        console.print(Padding(table, (1, 0)))

    console.print(
        Padding(
            f"{len(column_errors.keys())} column configuration errors:",
            (1, 0),
            style="bold dim cyan",
        )
    )
    for node_name, node_errors in column_errors.items():
        table = Table(
            title=node_name,
            title_justify="left",
            title_style="bold red",
            show_lines=True,
        )
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Column")
        table.add_column("Message", style="magenta")
        table.add_column("Type", style="red")

        for err in node_errors:
            table.add_row(err.field, err.column, err.message, err.type)

        console.print(Padding(table, (1, 0)))


def validate(manifest_path: str) -> None:
    manifest = WritableManifest.read_and_check_versions(manifest_path)

    table_errors = _validate_references(manifest)
    column_errors = _validate_column_references(manifest)
    num_errors = len(table_errors.keys()) + len(column_errors.keys())
    if num_errors > 0:
        _print_validation_errors(table_errors, column_errors)
        sys.exit(1)
