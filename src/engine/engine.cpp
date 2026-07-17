/// @file engine.cpp
/// Engine facade implementation.

#include <chessie/engine.hpp>

namespace chessie {

Engine::Engine(std::size_t tt_mb) : search_(tt_mb) {}

SearchResult Engine::search(Position& pos, const SearchLimits& limits) {
    return search_.search(pos, limits);
}

void Engine::cancel() noexcept {
    search_.cancel();
}

void Engine::set_tt_size(std::size_t mb) {
    search_.tt().resize(mb);
}

void Engine::clear_tt() {
    search_.tt().clear();
}

}  // namespace chessie
