\subsection*{Task 3: DotMotif: Searching for cortical structure}  %neo4j
\jordan{I'm currently reworking all of this. It's...pretty terrible. Hang tight.}
Connectome reconstruction data can be represented as directed graph where nodes are neurons and edges represent the (typed) directed synapses (i.e. information flow). \will{Do I need to explain this or is there adequate context in the rest of the doc?}

Prior neuroscience research points to recurring columnar structure of neocortex \cite{mountcastle} \cite{icecubes}; existing reconstructions of both invertebrates\cite{flyEM} as well as localized reconstructions of vertebrate CNS\cite{zebrafish?} demonstrate the presence of recurring structure. While these discoveries strongly support the columnar hypothesis, there currently exists no reliable mechanism by which repeating structure may be identified in a novel dataset without substantial human intervention.

We use the term "motif" to refer to statistically significant repeat of graph structure, and the term "computational primitive" to refer to a motif for which we know the biological function (e.g. 'noise reduction' or 'winner-takes-all').

Identifying motifs is a significant challenge because the scale of the raw anatomical imagery that spans multiple putative columns may reach terabyte or petabyte levels. Even if the structure of a motif for which we intend to search is \textit{known}, traversing multi-million-edge graphs with conventional subgraph-isomorphism algorithms is immensely time-consuming and computationally expensive.

\elizabeth{Can you please sanity-check this if you have a moment? I think I made this way more complicated than it had to be...}
Formally, for a known `haystack' graph $G = <V, E>$ and `needle' $N = <V', E'>$, the question of whether $V' \in V, E' \in E$ and a mapping $S$ exists where $(S(v_i), S(v_j)) \approx (v_i, v_j), (S(v_i), S(v_j)) \in N, (v_i, v_j) \in G$ is NP-hard. The runtimes of current state-of-the-art algorithms such as VF2 \cite{Cordella_2004} still remain prohibitively slow when run in-memory even on high-throughput compute resources.

In order to reduce the computational complexity of this task, we implement a multi-stage processing pipeline to ``compile'' motifs prior to performing a full-graph search. This both reduces the possibility of searching for biologically impossible motifs (e.g. motifs where a single cell acts both as an inhibitory as well as excitatory influence) as well as physically impossible motifs (e.g. if a designer requests that an edge $\overrightarrow{AB}$ both exist and does not exist \will{need help clarifying that}.

This processing pipeline software, dubbed \textit{dotmotif}, is a Python package that converts a domain-specific language (DSL) for describing motifs into a compiled, optimized derived form, and which then performs a search using one of a variety of supported graph search algorithms and databases. These systems include Neo4j \cite{neo4j} and networkx \cite{networkx}, among others.

\begin{figure}[t!]
\begin{center}
\includegraphics[width=\columnwidth]{figs/dotmotifschematic.png}
\end{center}
\vspace{-6mm}
\caption{The DotMotif software spans multiple pre-processing and optimization steps before a time-consuming search is carried out.\jordan{flesh out}}
\label{fig:dotmotif}
\vspace{-4mm}
\end{figure}

\subsubsection*{A domain-specific language for the description of motif structure}

In order to reduce the cognitive overhead of annotating a motif for search, we have developed the \texttt{dotmotif} DSL, a syntax designed to simplify the preprocessing steps leading to motif search (`Preprocessing' and `Compilation' in Fig. \ref{fig:dotmotif}.

The dotmotif DSL follows a simple set of rules to construct complex motifs. Each rule is applied to a hypothetical `query' graph, which is then optimized and located in the haystack graph.

\textbf{Edges.} Edges between nodes are notated with an arrow. The query

\begin{spverbatim}
A -> B
\end{spverbatim}

will return a list of every edge in the haystack graph.

\textbf{Negated edges.} Edges that \textit{must not} exist in the motif are notated with a negated arrow:
\begin{spverbatim}
A -> B
B ~> A
\end{spverbatim}

will return a list of every edge in the haystack graph for which the reciprocal edge does not exist.

\textbf{Edge types.} Edges may have `type' as well as an existance annotation. Edge type is indicated with square brackets:
\begin{spverbatim}
A -[inhibits] B
B ~[excites] A
\end{spverbatim}

will match every two nodes $(A, B)$ in the graph for which $A$ inhibits $B$ and $B$ \textit{does not} excite $A$.

\textbf{Macros.} Macros can be used to template repeated complex structure in a motif:

\begin{spverbatim}
# Nodes that are connected in only one direction:
unidirectional(n, m) {
    n -> m
    m ~> n
}

# All triangles for which edges exist in only one direction:
unidirectionalTriangle(x, y, z) {
    unidirectional(x, y)
    unidirectional(y, z)
    unidirectional(z, x)
}

unidirectionalTriangle(A, B, C)
unidirectionalTriangle(C, D, E)
\end{spverbatim}

will match graphs with unidirectional triangles between $A, B, C$ and $C, D, E$.

Using this existing software, we have implemented a query system that compiles a motif and searches a Neo4j graph database using a Cypher-exported version of that optimized subgraph structure.

\subsubsection*{High-level structure identification}

Once repeated motifs have been identified in the haystack graph, their spatial distribution may be used in order to identify candidate anatomies for cortical superstructure. We intend to leverage existing partial solutions to the challenge of converting sparse anatomical data to a measure of repeated structure \cite{superficialpatch} \cite{?}, and further expand these protocols to work on arbitrary, dense EM reconstructions.

One such (simple) measure of the biological validity of found structure is that of centroid distribution normality: A repeated columnar structure, according to our expectations \cite{?}, should tile in patterns of highly regular radius. Performing a discrete Fourier transform on the 2D coordinates of the centroids of these columns should yield a very strong single peak if the centroids are distributed regularly, and should yield noise if the centroids are distributed randomly. The normality of this FT result (derived using, for example, a Shapiro normality test) should be close to 1 in cases of regular motif repetition, and closer to 0 in cases of statistically insignificant motif repetition.
