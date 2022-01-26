(define (domain matchcellar)
     (:requirements :typing :durative-actions)
     (:types match fuse)
     (:predicates
          (handfree)
          (unused ?match - match)
          (mended ?fuse - fuse)
	  (light ?match - match))

     (:durative-action LIGHT_MATCH
          :parameters (?match - match)
          :duration (= ?duration 5)
          :condition (and
	       (at start (unused ?match)))
          :effect (and
		(at start (not (unused ?match)))
		(at start (light ?match))
		(at end (not (light ?match)))))


     (:durative-action MEND_FUSE
          :parameters (?fuse - fuse ?match - match)
          :duration (and (>= ?duration 4) (<= ?duration 4))
          :condition (and
               (at start (handfree))
	       (over all (light ?match)))
          :effect (and
               (at start (not (handfree)))
               (at end (mended ?fuse))
               (at end (handfree))))
)
