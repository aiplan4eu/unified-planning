/* 
 * Copyright (C) 2017 Universitat Politècnica de València
 *
 * This file is part of FMAP.
 *
 * FMAP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * FMAP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with FMAP. If not, see <http://www.gnu.org/licenses/>.
 */
package org.agreement_technologies.service.tools;

import java.util.*;

/**
 * CustomArrayList class implements a fast resizeable array.
 *
 * @param <E> Type for the array elements
 *
 * @author Oscar Sapena
 * @author Alejandro Torreno
 * @version %I%, %G%
 * @since 1.0
 */
public class CustomArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable {

    private int size;           // Current number of elements
    private transient E v[];    // Array to store the elements

    /**
     * Creates an empty list with an initial capacity.
     * 
     * @param capacity Initial capacity
     * @since 1.0
     */
    @SuppressWarnings("unchecked")
    public CustomArrayList(int capacity) {
        size = 0;
        v = (E[]) new Object[capacity];
    }

    /**
     * Creates an empty list with a default capacity (10 elements).
     * 
     * @since 1.0
     */
    public CustomArrayList() {
        this(10);
    }

    /**
     * Trims the number of elements to the specified number.
     * 
     * @param s New size for the list 
     * @since 1.0
     */
    public void trimToSize(int s) {
        this.size = s;
    }

    /**
     * Adds a new element avoiding repetitions.
     * 
     * @param value Elemento to add
     * @since 1.0
     */
    public void addNotRepeated(E value) {
        for (int i = 0; i < this.size; i++) {
            if (value.equals(v[i])) {
                return;
            }
        }
        this.add(value);
    }

    /**
     * Clears the list.
     * 
     * @since 1.0
     */
    @Override
    public void clear() {
        size = 0;
    }

    /**
     * Inserts a new element at the end of the list.
     * 
     * @param x Element to add
     * @since 1.0
     */
    public void insert(E x) {
        if (size == v.length) {
            v = java.util.Arrays.copyOf(v, v.length + (v.length >> 1));
        }
        v[size++] = x;
    }

    /**
     * Inserts a new element at the end of the list.
     * 
     * @param x Element to add
     * @return Always <code>true</code>
     * @since 1.0
     */
    @Override
    public boolean add(E x) {
        if (size == v.length) {
            v = java.util.Arrays.copyOf(v, v.length + (v.length >> 1));
        }
        v[size++] = x;
        return true;
    }

    /**
     * Removes the element in the given position. The last element is moved to
     * that position.
     * 
     * @param x Position of the element to remove
     * @since 1.0
     */
    public void removePosition(int x) {
        v[x] = v[--size];
    }

    /**
     * Gest the element in a given position.
     * 
     * @param index Position of the element to return
     * @return Element in the given position
     * @since 1.0
     */
    @Override
    public E get(int index) {
        return v[index];
    }

    /**
     * Gets the number of elements in this list.
     * 
     * @return Number of elements
     * @since 1.0
     */
    @Override
    public int size() {
        return size;
    }

    /**
     * Check if this list is empty.
     * 
     * @return <code>true</code>, if this list is empty; <code>false</code>,
     * otherwise
     * @since 1.0
     */
    @Override
    public boolean isEmpty() {
        return this.size == 0;
    }

    /**
     * Gets and erases the last element of the array
     *
     * @return Last element
     * @since 1.0
     */
    public E retrieve() {
        this.size--;
        return this.get(this.size);
    }

    /**
     * Appends an array to the end of this list.
     *
     * @param array Array to append
     * @since 1.0
     */
    public void append(CustomArrayList<E> array) {
        for (E v : array) {
            this.add(v);
        }
    }

    /**
     * Checks if the array includes a certain element.
     *
     * @param elem Element to check
     * @return <code>true</code>, if the array includes the element;
     * <code>false</code>, otherwise
     * @since 1.0
     */
    public boolean includes(E elem) {
        for (E val : this.v) {
            if (val == elem) {
                return true;
            }
        }
        return false;
    }
}
