(define (domain robots-domain)
(:requirements :typing :equality :fluents)
(:types surface place hoist agent - object
        truck - agent
        depot distributor - (either place agent)
        crate pallet - surface
)
(:predicates 
  (myAgent ?a - place)
  (clear_s ?s - surface)
  (clear ?h - hoist)
)
(:functions
  (located ?h - hoist) - place
  (at ?t - truck) - place
  (placed ?p - pallet) - place
  (pos ?c - crate) - place
  (pos_u ?c - crate) - truck
  (on ?c - crate) - hoist
  (on_u ?c - crate) - truck
  (on_s ?c - crate) - surface)
(:action LiftP
 :parameters (?h - hoist ?c - crate ?z - pallet ?p - place)
 :precondition (and (myAgent ?p) (= (located ?h) ?p) (= (placed ?z) ?p) (clear ?h) (= (pos ?c) ?p) (= (on_s ?c) ?z) (clear_s ?c))
 :effect (and (assign (on ?c) ?h) (not (clear_s ?c)) (not (clear ?h)) (clear_s ?z)))
(:action LiftC
 :parameters (?h - hoist ?c - crate ?z - crate ?p - place)
 :precondition (and (myAgent ?p) (= (located ?h) ?p) (= (pos ?z) ?p) (clear ?h) (= (pos ?c) ?p) (= (on_s ?c) ?z) (clear_s ?c))
 :effect (and (assign (on ?c) ?h) (not (clear_s ?c)) (not (clear ?h)) (clear_s ?z)))
(:action DropP
 :parameters (?h - hoist ?c - crate ?z - pallet ?p - place)
 :precondition (and (myAgent ?p) (= (located ?h) ?p) (= (placed ?z) ?p) (clear_s ?z) (= (on ?c) ?h) (not (clear_s ?c)) (not (clear ?h)))
 :effect (and (clear ?h) (clear_s ?c) (not (clear_s ?z)) (assign (on_s ?c) ?z)))
(:action DropC
 :parameters (?h - hoist ?c - crate ?z - crate ?p - place)
 :precondition (and (myAgent ?p) (= (located ?h) ?p) (= (pos ?z) ?p) (clear_s ?z) (= (on ?c) ?h) (not (clear_s ?c)) (not (clear ?h)))
 :effect (and (clear ?h) (clear_s ?c) (not (clear_s ?z)) (assign (on_s ?c) ?z)))
)

