# Complex brain-graph queries with DotMotif

> ## Abstract
> ...

## Introduction

Modern connectomics research commonly involves the conversion of microscopy imagery data into a graph representation of connectivity, where nodes represent neurons, and directed edges represent the synapses between them. This process enables researchers to convert terabytes or even petabytes of imagery into megabytes or gigabytes of graph data, which reduces the cost and complexity of interrogating the data. Though this graph representation takes substantially smaller compututational power to store and process, asking even the simplest questions of the resultant graphs may still exceed the computational power, timelines, and budgets of many research teams.

Some connectomics research teams have begun addressing this challenge by adopting existing large-scale graph management software, such as graph databases. These systems provide performant and cost-effective ways to manipulate larger-than-memory graphs, but tend to require familiarity with complex and nuanced graph query programming languages. Though graph databases continue to grow in popularity, this expertise is still rare in the biological sciences.

In order to enable all members of our research team to study the connectomes that we generate, we developed DotMotif, an intuitive but powerful graph query language designed to lower the activation-energy required to begin interrogating brain graphs. DotMotif acts as an interface to common graph management systems such as the networkx Python library or the Neo4j graph database, abstracting the intricacies of algorithm design and enabling researchers to focus on scientific inquiry.

Herein, we present the DotMotif software and discuss our architectural design that enables researchers to design queries agnostic of underlying technologies. We furthermore demonstrate DotMotif's utility by comparing its performance against manual query design, and finally share neuroscience discoveries we've made enabled by the DotMotif tool.

## Background

## Methods

## Results

## Discussion
