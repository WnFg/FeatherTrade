from __future__ import annotations

import os
from typing import List, Tuple

from src.trading_system.backtest.result import BacktestResult
from src.trading_system.modules.execution_engine import Side


class BacktestVisualizer:
    """
    Generates visualisation reports from a BacktestResult.

    Supported backends:
      - 'plotly'     → interactive HTML (default)
      - 'matplotlib' → static PNG

    If the chosen backend is unavailable, falls back automatically.
    If both are unavailable, exports a CSV summary.
    """

    def plot(
        self,
        result: BacktestResult,
        output_path: str = "backtest_report.html",
        backend: str = "plotly",
    ) -> str:
        """
        Generate and save a visualisation report.

        Returns the path of the saved file.
        """
        if backend == "plotly":
            try:
                return self._plot_plotly(result, output_path)
            except ImportError:
                print(
                    "[BacktestVisualizer] WARNING: plotly not installed. "
                    "Falling back to matplotlib."
                )
                # Ensure output path has .png extension for fallback
                png_path = os.path.splitext(output_path)[0] + ".png"
                try:
                    return self._plot_matplotlib(result, png_path)
                except ImportError:
                    print(
                        "[BacktestVisualizer] WARNING: matplotlib not installed either. "
                        "Exporting CSV summary."
                    )
                    return self._export_csv(result, output_path)
        else:
            try:
                png_path = output_path if output_path.endswith(".png") else os.path.splitext(output_path)[0] + ".png"
                return self._plot_matplotlib(result, png_path)
            except ImportError:
                print(
                    "[BacktestVisualizer] WARNING: matplotlib not installed. "
                    "Exporting CSV summary."
                )
                return self._export_csv(result, output_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_buy_sell_markers(
        self, result: BacktestResult
    ) -> Tuple[list, list, list, list]:
        """Split trades into BUY and SELL marker lists.

        Returns (buy_times, buy_prices, sell_times, sell_prices).
        """
        buy_times, buy_prices = [], []
        sell_times, sell_prices = [], []
        for trade in result.trades:
            if trade.side == Side.BUY:
                buy_times.append(trade.timestamp)
                buy_prices.append(trade.price)
            else:
                sell_times.append(trade.timestamp)
                sell_prices.append(trade.price)
        return buy_times, buy_prices, sell_times, sell_prices

    def _plot_plotly(self, result: BacktestResult, output_path: str) -> str:
        """Render an interactive 4-panel HTML report using Plotly."""
        import plotly.graph_objects as go  # type: ignore
        from plotly.subplots import make_subplots  # type: ignore

        buy_times, buy_prices, sell_times, sell_prices = self._compute_buy_sell_markers(result)

        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            subplot_titles=(
                f"{result.symbol} 价格走势 & 买卖点",
                "资金净值",
                "回撤",
                "持仓量",
            ),
            row_heights=[0.4, 0.2, 0.2, 0.2],
        )

        # --- Row 1: Price + buy/sell markers ---
        if result.bars:
            times = [b.timestamp for b in result.bars]
            closes = [b.close for b in result.bars]
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=closes,
                    mode="lines",
                    name="收盘价",
                    line=dict(color="#1f77b4", width=1.5),
                ),
                row=1, col=1,
            )

        if buy_times:
            fig.add_trace(
                go.Scatter(
                    x=buy_times,
                    y=buy_prices,
                    mode="markers",
                    name="买入",
                    marker=dict(
                        symbol="triangle-up",
                        size=12,
                        color="#2ca02c",
                    ),
                    hovertemplate="买入: %{y:.2f}<extra></extra>",
                ),
                row=1, col=1,
            )

        if sell_times:
            fig.add_trace(
                go.Scatter(
                    x=sell_times,
                    y=sell_prices,
                    mode="markers",
                    name="卖出",
                    marker=dict(
                        symbol="triangle-down",
                        size=12,
                        color="#d62728",
                    ),
                    hovertemplate="卖出: %{y:.2f}<extra></extra>",
                ),
                row=1, col=1,
            )

        # --- Row 2: Equity curve ---
        if not result.equity_curve.empty:
            fig.add_trace(
                go.Scatter(
                    x=result.equity_curve.index,
                    y=result.equity_curve.values,
                    mode="lines",
                    name="净值",
                    line=dict(color="#ff7f0e", width=1.5),
                ),
                row=2, col=1,
            )

        # --- Row 3: Drawdown ---
        if not result.drawdown_curve.empty:
            fig.add_trace(
                go.Scatter(
                    x=result.drawdown_curve.index,
                    y=(result.drawdown_curve.values * 100),
                    mode="lines",
                    name="回撤 %",
                    fill="tozeroy",
                    line=dict(color="#d62728", width=1),
                    fillcolor="rgba(214,39,40,0.2)",
                ),
                row=3, col=1,
            )

        # --- Row 4: Position ---
        if not result.position_curve.empty:
            fig.add_trace(
                go.Scatter(
                    x=result.position_curve.index,
                    y=result.position_curve.values,
                    mode="lines",
                    name="持仓量",
                    line=dict(color="#9467bd", width=1.5, shape="hv"),
                ),
                row=4, col=1,
            )

        # Layout
        metrics = result.metrics
        title = (
            f"回测报告 | {result.symbol} | "
            f"总收益: {metrics.get('total_return', 0):.2%} | "
            f"最大回撤: {metrics.get('max_drawdown', 0):.2%} | "
            f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f} | "
            f"胜率: {metrics.get('win_rate', 0):.2%}"
        )
        fig.update_layout(
            title=title,
            height=900,
            template="plotly_white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        )
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="净值 (元)", row=2, col=1)
        fig.update_yaxes(title_text="回撤 %", row=3, col=1)
        fig.update_yaxes(title_text="持仓量", row=4, col=1)

        fig.write_html(output_path)
        print(f"[BacktestVisualizer] HTML 报告已保存: {output_path}")
        return output_path

    def _plot_matplotlib(self, result: BacktestResult, output_path: str) -> str:
        """Render a static 4-panel PNG report using Matplotlib."""
        import matplotlib  # type: ignore
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt  # type: ignore
        import matplotlib.dates as mdates  # type: ignore

        buy_times, buy_prices, sell_times, sell_prices = self._compute_buy_sell_markers(result)

        fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(
            f"回测报告 | {result.symbol}\n"
            f"总收益: {result.metrics.get('total_return', 0):.2%}  "
            f"最大回撤: {result.metrics.get('max_drawdown', 0):.2%}  "
            f"Sharpe: {result.metrics.get('sharpe_ratio', 0):.2f}  "
            f"胜率: {result.metrics.get('win_rate', 0):.2%}",
            fontsize=11,
        )

        # Row 1: Price + markers
        ax1 = axes[0]
        if result.bars:
            times = [b.timestamp for b in result.bars]
            closes = [b.close for b in result.bars]
            ax1.plot(times, closes, color="#1f77b4", linewidth=1, label="收盘价")
        if buy_times:
            ax1.scatter(buy_times, buy_prices, marker="^", color="#2ca02c", s=80, zorder=5, label="买入")
        if sell_times:
            ax1.scatter(sell_times, sell_prices, marker="v", color="#d62728", s=80, zorder=5, label="卖出")
        ax1.set_ylabel("价格")
        ax1.legend(loc="upper left", fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Row 2: Equity
        ax2 = axes[1]
        if not result.equity_curve.empty:
            ax2.plot(result.equity_curve.index, result.equity_curve.values, color="#ff7f0e", linewidth=1)
        ax2.set_ylabel("净值 (元)")
        ax2.grid(True, alpha=0.3)

        # Row 3: Drawdown
        ax3 = axes[2]
        if not result.drawdown_curve.empty:
            dd_pct = result.drawdown_curve.values * 100
            ax3.fill_between(result.drawdown_curve.index, dd_pct, 0, color="#d62728", alpha=0.4)
            ax3.plot(result.drawdown_curve.index, dd_pct, color="#d62728", linewidth=0.8)
        ax3.set_ylabel("回撤 %")
        ax3.grid(True, alpha=0.3)

        # Row 4: Position
        ax4 = axes[3]
        if not result.position_curve.empty:
            ax4.step(result.position_curve.index, result.position_curve.values,
                     color="#9467bd", linewidth=1, where="post")
        ax4.set_ylabel("持仓量")
        ax4.grid(True, alpha=0.3)

        # Format x-axis
        ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[BacktestVisualizer] PNG 报告已保存: {output_path}")
        return output_path

    def _export_csv(self, result: BacktestResult, output_path: str) -> str:
        """Fallback: export equity curve and trades as CSV files."""
        import csv

        base = os.path.splitext(output_path)[0]
        eq_path = base + "_equity.csv"
        tr_path = base + "_trades.csv"

        # Equity curve
        with open(eq_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "equity"])
            for ts, eq in zip(result.equity_curve.index, result.equity_curve.values):
                writer.writerow([ts, eq])

        # Trades
        with open(tr_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "symbol", "side", "quantity", "price", "pnl"])
            for t in result.trades:
                writer.writerow([t.timestamp, t.symbol, t.side.value, t.quantity, t.price, t.pnl])

        print(f"[BacktestVisualizer] CSV 已保存: {eq_path}, {tr_path}")
        return eq_path
