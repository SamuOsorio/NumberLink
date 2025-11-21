class NumberlinkSolver:
    def __init__(self, archivo):
        self.tablero = []
        self.ancho = 0
        self.alto = 0
        self.pares = {}
        self.solucion = None
        self.cargar_tablero(archivo)
    
    def cargar_tablero(self, archivo):
        with open(archivo, 'r') as f:
            lineas = f.readlines()
            self.alto, self.ancho = map(int, lineas[0].strip().split())
            
            for i in range(1, self.alto + 1):
                if i < len(lineas):
                    fila = list(lineas[i].rstrip('\n').rstrip('\r'))                  
                    while len(fila) < self.ancho:
                        fila.append(' ')
                    self.tablero.append(fila[:self.ancho])
                else:
                    self.tablero.append([' '] * self.ancho)
        
        # Identificar pares de conectores
        for i in range(self.alto):
            for j in range(self.ancho):
                celda = self.tablero[i][j]
                if celda != ' ':
                    if celda not in self.pares:
                        self.pares[celda] = []
                    self.pares[celda].append((i, j))
    
    def print_tablero(self, tablero):
        """Imprime el tablero con formato"""
        # Línea superior
        print('+---' * self.ancho + '+')
        
        for i, fila in enumerate(tablero):
            # Contenido de la fila
            print('| ' + ' | '.join(fila) + ' |')
            
            # Línea divisoria
            print('+---' * self.ancho + '+')
    
    def distancia(self, p1, p2):
        """Calcula la distancia entre dos puntos"""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    def ordenar_pares_por_heuristica(self):
        """Ordena los pares por dificultad (más restringidos primero)"""
        puntuaciones_pares = []
        
        for conector, posiciones in self.pares.items():
            if len(posiciones) != 2:
                continue
            
            p1, p2 = posiciones
            
            # Heurística 1: distancia Manhattan (más cortos primero para este caso)
            d = self.distancia(p1, p2)
            
            # Heurística 2: conectores en esquinas/bordes
            puntuacion_esquina_borde = 0
            for p in [p1, p2]:
                # Esquinas
                if (p[0] == 0 or p[0] == self.alto - 1) and \
                   (p[1] == 0 or p[1] == self.ancho - 1):
                    puntuacion_esquina_borde += 30
                elif p[0] == 0 or p[0] == self.alto - 1 or \
                     p[1] == 0 or p[1] == self.ancho - 1:
                    puntuacion_esquina_borde += 15
            
            # Heurística 3: grado de libertad (menos vecinos libres = más restringido)
            libertad = 0
            for p in [p1, p2]:
                vecinos_libres = 0
                for ni, nj in self.get_vecinos(p):
                    if self.tablero[ni][nj] == ' ':
                        vecinos_libres += 1
                libertad += vecinos_libres
            
            # puntuacion: priorizar alta restricción (bajo libertad) y bordes
            # Distancia negativa para priorizar pares cercanos
            puntuacion = puntuacion_esquina_borde - libertad - d * 0.5
            puntuaciones_pares.append((puntuacion, conector))
        
        puntuaciones_pares.sort(reverse=True)
        return [conector for _, conector in puntuaciones_pares]
    
    def get_vecinos(self, pos):
        """Obtiene vecinos válidos de una posición"""
        i, j = pos
        vecinos = []
        
        # Orden: arriba, derecha, abajo, izquierda
        for di, dj in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.alto and 0 <= nj < self.ancho:
                vecinos.append((ni, nj))
        
        return vecinos
    
    def encontrar_caminos(self, inicio, fin, conector, tablero, max_caminos=None):
        """Encuentra múltiples caminos posibles usando búsqueda exhaustiva"""
        caminos = []
        
        def dfs(actual, camino, visitado):
            if max_caminos and len(caminos) >= max_caminos:
                return
            
            if actual == fin:
                caminos.append(camino[:])
                return
            
            for vecino in self.get_vecinos(actual):
                ni, nj = vecino
                
                if vecino in visitado:
                    continue
                
                celda = tablero[ni][nj]
                
                # Solo puede pasar por celdas vacías o el destino
                if celda != ' ' and vecino != fin:
                    continue
                
                # Poda más permisiva: permitir caminos muy largos
                if len(camino) > self.ancho * self.alto * 2:
                    continue
                
                visitado.add(vecino)
                camino.append(vecino)
                dfs(vecino, camino, visitado)
                camino.pop()
                visitado.remove(vecino)
        
        visitado = {inicio}
        dfs(inicio, [inicio], visitado)
        
        # Ordenar caminos por calidad (más cortos y directos primero)
        def camino_puntuacion(camino):
            longitud = len(camino)
            giros = 0
            for i in range(2, len(camino)):
                dir1 = (camino[i-1][0] - camino[i-2][0], camino[i-1][1] - camino[i-2][1])
                dir2 = (camino[i][0] - camino[i-1][0], camino[i][1] - camino[i-1][1])
                if dir1 != dir2:
                    giros += 1
            return longitud + giros * 0.3
        
        caminos.sort(key=camino_puntuacion)
        return caminos
    
    def marcar_camino(self, tablero, camino, conector):
        """Marca un camino en el tablero con el carácter del conector"""
        for pos in camino:
            tablero[pos[0]][pos[1]] = conector
    
    def desmarcar_camino(self, tablero, camino, posiciones_originales):
        """Desmarca un camino del tablero (excepto las posiciones originales)"""
        for pos in camino:
            if pos not in posiciones_originales:
                tablero[pos[0]][pos[1]] = ' '
    
    def contar_celdas_vacias(self, tablero):
        """Cuenta celdas vacías"""
        contador = 0
        for fila in tablero:
            contador += fila.count(' ')
        return contador
    
    def verificar_puntos_muertos(self, tablero):
        """Verifica si hay celdas vacías que formarían callejones sin salida"""
        for i in range(self.alto):
            for j in range(self.ancho):
                if tablero[i][j] == ' ':
                    vecinos_vacios = 0
                    for ni, nj in self.get_vecinos((i, j)):
                        if tablero[ni][nj] == ' ':
                            vecinos_vacios += 1
                    # Una celda vacía con 0 o 1 vecino vacío es problemática
                    # (excepto si es la última celda)
                    if vecinos_vacios == 0:
                        return True
        return False
    
    def contar_regiones(self, tablero):
        """Cuenta el número de regiones desconectadas de celdas vacías"""
        visitado = set()
        regiones = 0
        
        for i in range(self.alto):
            for j in range(self.ancho):
                if tablero[i][j] == ' ' and (i, j) not in visitado:
                    # BFS para marcar toda la región
                    regiones += 1
                    cola = [(i, j)]
                    visitado.add((i, j))
                    
                    while cola:
                        ci, cj = cola.pop(0)
                        for ni, nj in self.get_vecinos((ci, cj)):
                            if (ni, nj) not in visitado and tablero[ni][nj] == ' ':
                                visitado.add((ni, nj))
                                cola.append((ni, nj))
        
        return regiones
    
    def backtrack(self, tablero, pares_ordenados, index, profundidad=0):
        """Algoritmo de backtracking con heurísticas"""
        # Caso base: todos los pares conectados
        if index == len(pares_ordenados):
            # Verificar que no queden espacios vacíos
            if self.contar_celdas_vacias(tablero) == 0:
                return [fila[:] for fila in tablero]
            return None
        
        conector = pares_ordenados[index]
        inicio, fin = self.pares[conector]
        
        # Encontrar múltiples caminos posibles
        if profundidad < 3:  # Primeros 3 conectores: exploración exhaustiva
            caminos = self.encontrar_caminos(inicio, fin, conector, tablero, max_caminos=None)
        else:  # Conectores restantes
            caminos = self.encontrar_caminos(inicio, fin, conector, tablero, max_caminos=2000)
        
        if not caminos:
            return None
        
        # Probar cada camino
        for camino_idx, camino in enumerate(caminos):
            # Marcar camino en el tablero
            self.marcar_camino(tablero, camino, conector)
            
            # Continuar con el siguiente par
            result = self.backtrack(tablero, pares_ordenados, index + 1, profundidad + 1)
            if result is not None:
                return result
            
            # Backtrack: deshacer cambios
            self.desmarcar_camino(tablero, camino, [inicio, fin])
        
        return None
    
    def solve(self):
        """Resuelve el tablero de Numberlink"""
        print("TABLERO DE ENTRADA:")
        self.print_tablero(self.tablero)
        print()
        
        # Copiar tablero original
        tablero = [fila[:] for fila in self.tablero]
        
        # Probar diferentes órdenes de resolución
        ordenes_a_probar = [
            self.ordenar_pares_por_heuristica(),  # Heurística
            list(self.pares.keys()),          # Orden original
            list(reversed(self.pares.keys())) # Orden inverso
        ]
        
        for idx, pares_ordenados in enumerate(ordenes_a_probar):
            tablero_copy = [fila[:] for fila in self.tablero]
            solucion = self.backtrack(tablero_copy, pares_ordenados, 0)
            
            if solucion:
                print("TABLERO DE SALIDA:")
                self.print_tablero(solucion)
                self.solucion = solucion

                with open('numberlink_solucion.txt', 'w') as f:
                    f.write(f"{self.alto} {self.ancho}\n")
                    for fila in solucion:
                        f.write(''.join(fila) + '\n')
                return True
        
        print("No se encontró solución")
        return False


if __name__ == "__main__":
    import sys

    archivo = sys.argv[1] if len(sys.argv) > 1 else "numberlink_00.txt"
    
    solver = NumberlinkSolver(archivo)
    solver.solve()
