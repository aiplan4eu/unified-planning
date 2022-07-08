(define (problem BLOCKS-4-0)
(:domain ma-blocksworld)
(:objects
 r0 r1 r2 r3 - robot
 d b a c - block
)
(:shared-data
  ((on ?b - block) - block)
  (ontable ?b - block)
  (clear ?b - block)
  ((holding ?r - robot) - block) - 
(either r0 r2 r3)
)
(:init
 (myAgent r1)
 (= (holding r0) nob)
 (= (holding r1) nob)
 (= (holding r2) nob)
 (= (holding r3) nob)
 (clear d)
 (ontable d)
 (= (on d) nob)
 (clear b)
 (ontable b)
 (= (on b) nob)
 (clear a)
 (ontable a)
 (= (on a) nob)
 (clear c)
 (ontable c)
 (= (on c) nob)
)
(:global-goal (and
 (= (on d) c)
 (= (on c) b)
 (= (on b) a)
)))
