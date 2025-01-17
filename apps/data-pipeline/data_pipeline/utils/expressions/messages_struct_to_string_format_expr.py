import polars as pl


def get_messages_struct_to_string_format_expr(partner_names: dict[str, str]) -> pl.Expr:
    return (
        pl.col("messages_struct")
        .list.eval(
            pl.concat_str(
                [
                    pl.lit("From: "),
                    pl.when(pl.element().struct.field("from").eq("me"))
                    .then(pl.lit(partner_names["me"]))
                    .otherwise(pl.element().struct.field("from")),
                    pl.lit(", To: "),
                    pl.when(pl.element().struct.field("to").eq("me"))
                    .then(pl.lit(partner_names["me"]))
                    .otherwise(pl.element().struct.field("to")),
                    pl.lit(", Date: "),
                    pl.element().struct.field("date"),
                    pl.lit(", Time: "),
                    pl.element().struct.field("time"),
                    pl.lit(", Content: "),
                    pl.element().struct.field("content"),
                ]
            )
        )
        .list.join("\n")
    )
