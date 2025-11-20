class NumberlinkSolver:
    def __init__(self, filename):
        self.board = []
        self.width = 0
        self.height = 0
        self.pairs = {}
        self.solution = None
        self.load_board(filename)
    
    def load_board(self, filename):
        """Carga el tablero desde un archivo"""
        with open(filename, 'r') as f:
            lines = f.readlines()
            self.height, self.width = map(int, lines[0].strip().split())
            
            for i in range(1, self.height + 1):
                if i < len(lines):
                    row = list(lines[i].rstrip('\n'))
                    # Ajustar longitud de la fila
                    while len(row) < self.width:
                        row.append(' ')
                    self.board.append(row[:self.width])
                else:
                    self.board.append([' '] * self.width)
        
        # Identificar pares de conectores
        for i in range(self.height):
            for j in range(self.width):
                cell = self.board[i][j]
                if cell != ' ':
                    if cell not in self.pairs:
                        self.pairs[cell] = []
                    self.pairs[cell].append((i, j))
    
    def print_board(self, board):
        """Imprime el tablero"""
        for row in board:
            print(''.join(row))
    
    def print_board_with_lines(self, board):
        """Imprime el tablero con líneas visuales para los caminos"""
        print(f"\n  ", end="")
        for j in range(self.width):
            print(f"  {j} ", end="")
        print()
        
        for i in range(self.height):
            # Línea superior de la fila
            print(f"{i} ", end="")
            for j in range(self.width):
                print("+---", end="")
            print("+")
            
            # Contenido de la celda
            print("  ", end="")
            for j in range(self.width):
                cell = board[i][j]
                
                # Mostrar celda
                print(f"| {cell} ", end="")
                
            print("|")
        
        # Línea inferior final
        print("  ", end="")
        for j in range(self.width):
            print("+---", end="")
        print("+")

    
    def manhattan_distance(self, p1, p2):
        """Calcula la distancia Manhattan entre dos puntos"""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    def order_pairs_by_heuristic(self):
        """Ordena los pares por dificultad (más restringidos primero)"""
        pair_scores = []
        
        for connector, positions in self.pairs.items():
            if len(positions) != 2:
                continue
            
            p1, p2 = positions
            
            # Heurística 1: distancia Manhattan
            distance = self.manhattan_distance(p1, p2)
            
            # Heurística 2: conectores en esquinas/bordes
            edge_score = 0
            for p in [p1, p2]:
                # Esquinas
                if (p[0] == 0 or p[0] == self.height - 1) and \
                   (p[1] == 0 or p[1] == self.width - 1):
                    edge_score += 20
                # Bordes
                elif p[0] == 0 or p[0] == self.height - 1 or \
                     p[1] == 0 or p[1] == self.width - 1:
                    edge_score += 10
            
            # Heurística 3: grado de libertad (menos vecinos libres = más restringido)
            freedom = 0
            for p in [p1, p2]:
                free_neighbors = 0
                for ni, nj in self.get_neighbors(p):
                    if self.board[ni][nj] == ' ':
                        free_neighbors += 1
                freedom += free_neighbors
            
            # Score: priorizar alta restricción (bajo freedom) y bordes
            score = edge_score - freedom + distance
            pair_scores.append((score, connector))
        
        pair_scores.sort(reverse=True)
        return [connector for _, connector in pair_scores]
    
    def get_neighbors(self, pos):
        """Obtiene vecinos válidos de una posición"""
        i, j = pos
        neighbors = []
        
        # Orden: arriba, derecha, abajo, izquierda
        for di, dj in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.height and 0 <= nj < self.width:
                neighbors.append((ni, nj))
        
        return neighbors
    
    def find_all_paths(self, start, end, connector, board, max_paths=500):
        """Encuentra múltiples caminos posibles usando búsqueda exhaustiva"""
        all_paths = []
        
        def dfs(current, path, visited):
            if len(all_paths) >= max_paths:
                return
            
            if current == end:
                all_paths.append(path[:])
                return
            
            for neighbor in self.get_neighbors(current):
                ni, nj = neighbor
                
                if neighbor in visited:
                    continue
                
                cell = board[ni][nj]
                
                # Solo puede pasar por celdas vacías o el destino
                if cell != ' ' and neighbor != end:
                    continue
                
                # Poda más permisiva: permitir caminos más largos
                if len(path) > self.width * self.height:
                    continue
                
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)
        
        visited = {start}
        dfs(start, [start], visited)
        
        # Ordenar caminos por calidad (más cortos y directos primero)
        def path_score(path):
            length = len(path)
            turns = 0
            for i in range(2, len(path)):
                dir1 = (path[i-1][0] - path[i-2][0], path[i-1][1] - path[i-2][1])
                dir2 = (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
                if dir1 != dir2:
                    turns += 1
            return length + turns * 0.5
        
        all_paths.sort(key=path_score)
        return all_paths
    
    def mark_path(self, board, path, connector):
        """Marca un camino en el tablero con el carácter del conector"""
        for pos in path:
            board[pos[0]][pos[1]] = connector
    
    def unmark_path(self, board, path, original_positions):
        """Desmarca un camino del tablero (excepto las posiciones originales)"""
        for pos in path:
            if pos not in original_positions:
                board[pos[0]][pos[1]] = ' '
    
    def count_empty_cells(self, board):
        """Cuenta celdas vacías"""
        count = 0
        for row in board:
            count += row.count(' ')
        return count
    
    def check_reachability(self, board):
        """Verifica que todas las celdas vacías sean alcanzables entre sí"""
        # Encontrar primera celda vacía
        start = None
        empty_count = 0
        for i in range(self.height):
            for j in range(self.width):
                if board[i][j] == ' ':
                    empty_count += 1
                    if start is None:
                        start = (i, j)
        
        if empty_count == 0:
            return True
        
        if start is None:
            return True
        
        # BFS para contar celdas alcanzables
        visited = {start}
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            for neighbor in self.get_neighbors(current):
                ni, nj = neighbor
                if neighbor not in visited and board[ni][nj] == ' ':
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Si todas las celdas vacías son alcanzables, OK
        return len(visited) == empty_count
    
    def backtrack(self, board, ordered_pairs, index, depth=0):
        """Algoritmo de backtracking con heurísticas"""
        # Caso base: todos los pares conectados
        if index == len(ordered_pairs):
            # Verificar que no queden espacios vacíos
            if self.count_empty_cells(board) == 0:
                return [row[:] for row in board]  # Retornar copia
            return None
        
        connector = ordered_pairs[index]
        start, end = self.pairs[connector]
        
        # Encontrar múltiples caminos posibles
        paths = self.find_all_paths(start, end, connector, board)
        
        if not paths:
            return None
        
        # Probar cada camino
        for path_idx, path in enumerate(paths):
            # Marcar camino en el tablero
            self.mark_path(board, path, connector)
            
            # Continuar con el siguiente par (sin verificaciones restrictivas)
            result = self.backtrack(board, ordered_pairs, index + 1, depth + 1)
            if result is not None:
                return result
            
            # Backtrack: deshacer cambios
            self.unmark_path(board, path, [start, end])
        
        return None
    
    def solve(self):
        """Resuelve el tablero de Numberlink"""
        """print("TABLERO ORIGINAL:")
        self.print_board(self.board)"""
        self.print_board_with_lines(self.board)
        print(f"\nTablero: {self.width}x{self.height}")
        print("\nResolviendo...\n")
        
        # Copiar tablero original
        board = [row[:] for row in self.board]
        
        # Probar diferentes órdenes de resolución
        orders_to_try = [
            self.order_pairs_by_heuristic(),  # Heurística
            list(self.pairs.keys()),          # Orden original
            list(reversed(self.pairs.keys())) # Orden inverso
        ]
        
        for idx, ordered_pairs in enumerate(orders_to_try):
            print(f"Intento {idx + 1} - Orden: {ordered_pairs}")
            board_copy = [row[:] for row in self.board]
            solution = self.backtrack(board_copy, ordered_pairs, 0)
            
            if solution:
                print("\n✓ SOLUCIÓN ENCONTRADA:")
                self.print_board(solution)
                print("\nCON LÍNEAS:")
                self.print_board_with_lines(solution)
                self.solution = solution
                
                # Guardar en archivo
                with open('numberlink_solution.txt', 'w') as f:
                    f.write(f"{self.height} {self.width}\n")
                    for row in solution:
                        f.write(''.join(row) + '\n')
                print("\n✓ Solución guardada en 'numberlink_solution.txt'")
                return True
            else:
                print("  ✗ No encontró solución con este orden\n")
        
        print("✗ No se encontró solución después de probar múltiples órdenes")
        return False


# Uso del solver
if __name__ == "__main__":
    import sys
    
    # Permitir especificar archivo por línea de comandos
    filename = sys.argv[1] if len(sys.argv) > 1 else "numberlink_00.txt"
    
    solver = NumberlinkSolver(filename)
    solver.solve()