(define (domain elevators)
(:requirements :typing :equality :fluents)
(:types passenger count - object
        elevator - agent
        slow-elevator fast-elevator - elevator)
(:predicates (myAgent ?e - elevator)
	(reachable-floor ?lift - elevator ?floor - count)
	(above ?floor1 - count ?floor2 - count)
	(can-hold ?lift - elevator ?n - count))
(:functions
	(at ?person - passenger) - (either count elevator)
	(lift-at ?lift - elevator) - count
	(passengers ?lift - elevator) - count
	(next ?n - count) - count)
(:action move-up-slow
  :parameters (?lift - slow-elevator ?f1 - count ?f2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f1) (above ?f1 ?f2) (reachable-floor ?lift ?f2))
  :effect (and (assign (lift-at ?lift) ?f2)))
(:action move-down-slow
  :parameters (?lift - slow-elevator ?f1 - count ?f2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f1) (above ?f2 ?f1) (reachable-floor ?lift ?f2))
  :effect (and (assign (lift-at ?lift) ?f2)))
(:action move-up-fast
  :parameters (?lift - fast-elevator ?f1 - count ?f2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f1) (above ?f1 ?f2) (reachable-floor ?lift ?f2))
  :effect (and (assign (lift-at ?lift) ?f2)))
(:action move-down-fast
  :parameters (?lift - fast-elevator ?f1 - count ?f2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f1) (above ?f2 ?f1) (reachable-floor ?lift ?f2))
  :effect (and (assign (lift-at ?lift) ?f2)))
(:action board
  :parameters (?p - passenger ?lift - elevator ?f - count ?n1 - count ?n2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f) (= (at ?p) ?f) (= (passengers ?lift) ?n1) (= (next ?n1) ?n2) (can-hold ?lift ?n2))
  :effect (and (assign (at ?p) ?lift) (assign (passengers ?lift) ?n2)))
(:action leave
  :parameters (?p - passenger ?lift - elevator ?f - count ?n1 - count ?n2 - count)
  :precondition (and (myAgent ?lift) (= (lift-at ?lift) ?f) (= (at ?p) ?lift) (= (passengers ?lift) ?n1) (= (next ?n2) ?n1))
  :effect (and (assign (at ?p) ?f) (assign (passengers ?lift) ?n2))))
