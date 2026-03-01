/// @file pybind_module.cpp
/// pybind11 bindings for the C++ chess engine.
///
/// Exposes `_chessie_engine` Python module with an `Engine` class.
/// Communication uses FEN strings (Position) and UCI strings (Move)
/// for maximum decoupling between Python and C++ types.

#include <chessie/engine.hpp>
#include <chessie/magic.hpp>

#include <mutex>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <tuple>

namespace py = pybind11;

namespace {

/// One-time initialisation of magic bitboard tables.
std::once_flag g_magic_init_flag;
void ensure_magic_init() {
    std::call_once(g_magic_init_flag, chessie::magic::init);
}

}  // namespace

PYBIND11_MODULE(_chessie_engine, m) {
    m.doc() = "Native C++ chess engine for Chessie (pybind11)";

    // Ensure magic tables are ready as soon as the module is imported.
    ensure_magic_init();

    // ── Engine class ────────────────────────────────────────────────────
    py::class_<chessie::Engine>(m, "Engine")
        .def(py::init<std::size_t>(), py::arg("tt_mb") = 64,
             "Create an engine with a transposition table of *tt_mb* megabytes.")

        .def(
            "search",
            [](chessie::Engine& self, const std::string& fen, int max_depth,
               int64_t time_limit_ms) -> py::tuple {
                chessie::Position pos = chessie::Position::from_fen(fen);
                chessie::SearchLimits limits;
                limits.max_depth = max_depth;
                limits.time_limit_ms = time_limit_ms;

                chessie::SearchResult result;
                {
                    // Release the GIL during the search so Python threads
                    // (e.g. the cancel callback) can run concurrently.
                    py::gil_scoped_release release;
                    result = self.search(pos, limits);
                }

                // Convert the best move to a UCI string (empty if null).
                std::string uci_move;
                if (!result.best_move.is_null()) {
                    uci_move = result.best_move.uci();
                }
                return py::make_tuple(uci_move, result.score_cp, result.depth,
                                      static_cast<int64_t>(result.nodes));
            },
            py::arg("fen"), py::arg("max_depth") = 64, py::arg("time_limit_ms") = -1,
            R"doc(Run an alpha-beta search on the position given by *fen*.

Returns a tuple ``(uci_move, score_cp, depth, nodes)``.
*uci_move* is an empty string when the position is already checkmate
or stalemate.)doc")

        .def("cancel", &chessie::Engine::cancel, "Cancel a running search (thread-safe).")

        .def("set_tt_size", &chessie::Engine::set_tt_size, py::arg("mb"),
             "Resize the transposition table (clears it).")

        .def("clear_tt", &chessie::Engine::clear_tt, "Clear the transposition table.");
}
