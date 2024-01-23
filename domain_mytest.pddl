(define (domain robot-domain)
 (:requirements :strips :typing :negative-preconditions :durative-actions)
 (:types location robot package)
 (:predicates (robot_at ?loc - location ?robot - robot) (connected ?l_from - location ?l_to - location) (robot_empty ?robot - robot) (loc_empty ?loc - location) (pack_empty ?loc - location) (robot_carry ?robot - robot ?p - package) (pack_at ?loc - location ?p - package))
 (:functions (cost ?l_from - location ?l_to - location) (battery_level))
 (:durative-action move
  :parameters ( ?r - robot ?l_from - location ?l_to - location)
  :duration (= ?duration (cost ?l_from ?l_to))
  :condition (and (at start (connected ?l_from ?l_to))(at start (robot_at ?l_from ?r))(at start (loc_empty ?l_to)))
  :effect (and 
                (at start (not (loc_empty ?l_to))) 
                (at start (not (robot_at ?l_from ?r))) 
                (at end (robot_at ?l_to ?r)) 
                (at end (loc_empty ?l_from)) 
                (decrease (battery_level) (* #t (* 10 (battery_level))))  
          )
 )
 (:durative-action load
  :parameters ( ?r - robot ?loc - location ?p - package)
  :duration (= ?duration 2)
  :condition (and (at start (robot_at ?loc ?r))(over all (robot_at ?loc ?r))(at end (robot_at ?loc ?r))(at start (robot_empty ?r))(at start (pack_at ?loc ?p))(at start (not (pack_empty ?loc))))
  :effect (and (at start (not (robot_empty ?r))) (at end (not (pack_at ?loc ?p))) (at end (robot_carry ?r ?p)) (at end (pack_empty ?loc))))
 (:durative-action unload
  :parameters ( ?r - robot ?loc - location ?p - package)
  :duration (= ?duration 3)
  :condition (and (at start (robot_at ?loc ?r))(over all (robot_at ?loc ?r))(at end (robot_at ?loc ?r))(at start (not (robot_empty ?r)))(at start (robot_carry ?r ?p))(at start (pack_empty ?loc)))
  :effect (and (at end (robot_empty ?r)) (at end (pack_at ?loc ?p)) (at end (not (pack_empty ?loc))) (at start (not (robot_carry ?r ?p)))))
)
