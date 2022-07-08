(define (domain ma-blocksworld)
(:requirements :typing :equality :fluents)
(:types
    robot - agent
    block - object)
(:constants
  nob - block)
(:predicates
  (myAgent ?x - robot)
  (clear ?x - block)
  (ontable ?x - block))
(:functions
  (on ?x - block) - block
  (holding ?x - robot) - block)
(:action pickup
:parameters (?ob - block ?r - robot)
:precondition (and (myAgent ?r) (= (on ?ob) nob) (ontable ?ob) (clear ?ob)(= (holding ?r) nob))
:effect (and (assign (holding ?r) ?ob) (not (ontable ?ob))(not (clear ?ob))))
(:action putdown
:parameters (?ob - block ?r - robot)
:precondition (and (myAgent ?r) (= (holding ?r) ?ob))
:effect (and (assign (holding ?r) nob)(ontable ?ob)(clear ?ob)))
(:action stack
:parameters (?ob - block ?uob - block ?r - robot)
:precondition (and (myAgent ?r) (clear ?uob) (= (holding ?r) ?ob))
:effect (and (assign (holding ?r) nob) (clear ?ob) (assign (on ?ob) ?uob) (not (clear ?uob))))
(:action unstack
:parameters (?ob - block ?uob - block ?r - robot)
:precondition (and (myAgent ?r) (= (on ?ob) ?uob) (clear ?ob) (= (holding ?r) nob))
:effect (and (assign (holding ?r) ?ob) (clear ?uob) (assign (on ?ob) nob) (not (clear ?ob)))))
