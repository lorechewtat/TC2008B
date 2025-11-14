/*
 * Script to draw a complex shape in 2D
 *
 * Lorena Estefania Chewtat Torres
 * 2025-11-10
 */


'use strict';

import * as twgl from 'twgl-base.js';
import { M3 } from './A01785378-2d-libs.js';
import GUI from 'lil-gui';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

void main() {
    // Multiply the matrix by the vector, adding 1 to the vector to make
    // it the correct size. Then keep only the two first components
    vec2 position = (u_transforms * vec3(a_position, 1)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    //gl_Position = vec4(clipSpace[0], clipSpace[1] * -1.0, 0, 1);
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
}
`;

const fsGLSL = `#version 300 es
precision highp float;

uniform vec4 u_color;

out vec4 outColor;

void main() {
    outColor = u_color;
}
`;

//Class to create any shape in 2D
class Object2D {
    constructor(id,
        position=[0, 0, 0],
        rotation=[0, 0, 0],
        scale=[1, 1, 1],
        color=[Math.random(), Math.random(), Math.random(), 1.0],
        arrays = {
            a_position: {
                numComponents: 2,
                data: []},
            a_colors: { 
                numComponents: 4,
                data: []},
            indices: {
                numComponents: 3,
                data: []}
        }){

        this.id = id;

        // Initial transformations
        this.position = {
            x: position[0],
            y: position[1],
            z: 0,
        };

        this.rotDeg = {
            x: 0,
            y: 0,
            z: rotation[2],
        };
        this.rotRad = {
            x: 0,
            y: 0,
            z: rotation[2] * Math.PI / 180,
        };
        this.scale = {
            x: scale[0],
            y: scale[1],
            z: 1,
        };

        this.matrix = M3.identity();
        // Materials and colors
        this.color = color;
        this.shininess = 100;
        this.texture = undefined;
        // Properties for rendering in WebGL
        this.arrays = arrays;
        this.bufferInfo = undefined;
        this.vao = undefined;
    }

    setPosition(position) {
        this.position = {
            x: position[0],
            y: position[1],
            z: 0,
        };
    }

    // Return the position as an array
    get posArray() {
        return [this.position.x, this.position.y, 0];
    }

    // Return the scale as an array
    get scaArray() {
        return [this.scale.x, this.scale.y, 1];
    }

    // Set up the WebGL components for an object
    prepareVAO(gl, programInfo, arrays) {
        this.arrays = arrays;
        this.bufferInfo = twgl.createBufferInfoFromArrays(gl, this.arrays);
        this.vao = twgl.createVAOFromBufferInfo(gl, programInfo, this.bufferInfo);
    }

    // Copy an existing vao
    setVAO(vao, bufferInfo) {
        this.vao = vao;
        this.bufferInfo = bufferInfo;
    }
};

// Structure for the global data of all objects
const objects = {
    border: new Object2D(
        'border',
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0, 1.0],
    ),

    face: new Object2D(
        'face',
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [1, 0.9, 0, 1.0],
    ),

    right_eye : new Object2D(
        'right_eye',
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [0.0078, 0, 0.0196, 1.0],
    ),

    left_eye : new Object2D(
        'left_eye',
        [0, 0, 0],  
        [0, 0, 0],
        [1, 1, 1],
        [0.0078, 0, 0.0196, 1.0],
    ),

    mouth : new Object2D(
        'mouth',
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [0.8627, 0.180, 0.1372, 1.0],

    ),

    pivot : new Object2D(
        'pivot',
        [0, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
        [0.392, 0.392, 0.392, 1]
    ),

}

// Create the data for the mouth shape
function mouthShape() {
    let arrays = {
        a_position: {
            numComponents: 2,
            data: [
                // vertices
                40, 10,
                50, 30,
                65, 45,
                135, 45,
                150, 30,
                160, 10,

                
            ]
        },
        indices: {
            numComponents: 3,
            data: [
                // triangles
                0, 1, 5,
                1, 2, 5,
                2, 3, 5,
                3, 4, 5,

            ]
        }
    };

    return arrays;
}

// Create the data for the vertices of the polyton, as an object with two arrays
function generateData(sides, centerX, centerY, radius) {
    // The arrays are initially empty
    let arrays =
    {
        // Two components for each position in 2D
        a_position: { numComponents: 2, data: [] },
        // Four components for a color (RGBA)
        a_color:    { numComponents: 4, data: [] },
        // Three components for each triangle, the 3 vertices
        indices:  { numComponents: 3, data: [] }
    };

    // Initialize the center vertex, at the origin and with white color
    arrays.a_position.data.push(centerX);
    arrays.a_position.data.push(centerY);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);
    arrays.a_color.data.push(1);

    let angleStep = 2 * Math.PI / sides;
    // Loop over the sides to create the rest of the vertices
    for (let s=0; s<sides; s++) {
        let angle = angleStep * s;
        // Generate the coordinates of the vertex
        let x = centerX + Math.cos(angle) * radius;
        let y = centerY + Math.sin(angle) * radius;
        arrays.a_position.data.push(x);
        arrays.a_position.data.push(y);
        // Generate a random color for the vertex
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(Math.random());
        arrays.a_color.data.push(1);
        // Define the triangles, in counter clockwise order
        arrays.indices.data.push(0);
        arrays.indices.data.push(s + 1);
        arrays.indices.data.push(((s + 2) <= sides) ? (s + 2) : 1);
    }
    console.log(arrays);

    return arrays;
}


// Initialize the WebGL environmnet
function main() {
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Generate each object's data
    let border_face = generateData(50, 100, 0, 97); // Border
    let face = generateData(50, 100, 0, 85); // Face
    let right_eye = generateData(50, 50, -20, 10); // Right eye
    let left_eye = generateData(50, 150,-20, 10); // Left eye
    let mouth = mouthShape(); // Mouth
    let pivot = generateData(4, 0, 0, 30); // Pivot 

    // Arrays
    objects.border.arrays = border_face;
    objects.face.arrays = face;
    objects.right_eye.arrays = right_eye;
    objects.left_eye.arrays = left_eye;
    objects.mouth.arrays = mouth;
    objects.pivot.arrays = pivot;

    // Initial positions
    objects.border.setPosition([gl.canvas.width / 2, gl.canvas.height / 2]);
    objects.pivot.setPosition([gl.canvas.width / 2 - 60, gl.canvas.height / 2]);

    //Position all objects according to the border position
    objects.face.setPosition(objects.border.posArray);
    objects.right_eye.setPosition(objects.border.posArray);
    objects.left_eye.setPosition(objects.border.posArray);
    objects.mouth.setPosition(objects.border.posArray);

    // Set up the UI
    setupUI(gl);

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    for (const object of Object.values(objects)) {
        object.prepareVAO(gl, programInfo, object.arrays);
    }

    drawScene(gl, programInfo);
}

// Function to do the actual display of the objects
function drawScene(gl, programInfo) {
    gl.useProgram(programInfo.program);

    for (const object of Object.values(objects)) {
        let transforms = M3.identity();

        // If the object is the pivot, only apply its translation
        if (object.id === 'pivot') {
            transforms = M3.multiply(M3.translation(object.posArray), transforms);
        } else {
            // For the other objects, apply the border's transformations
            transforms = M3.multiply(M3.scale(objects.border.scaArray), transforms);
            transforms = M3.multiply(M3.translation(objects.border.posArray), transforms);
            
            transforms = M3.multiply(M3.translation([-objects.pivot.position.x, -objects.pivot.position.y]), transforms);
            transforms = M3.multiply(M3.rotation(objects.border.rotRad.z), transforms);
            transforms = M3.multiply(M3.translation(objects.pivot.posArray), transforms);

            
        }

        let uniforms =
        {
            u_resolution: [gl.canvas.width, gl.canvas.height],
            u_transforms: transforms,
            u_color: object.color,
        }

        twgl.setUniforms(programInfo, uniforms);
        gl.bindVertexArray(object.vao);
        twgl.drawBufferInfo(gl, object.bufferInfo);
    }


    requestAnimationFrame(() => drawScene(gl, programInfo));
}

function setupUI(gl)
{
    const gui = new GUI();

    const traFolder = gui.addFolder('Face Translation');
    traFolder.add(objects.border.position, 'x', 0, gl.canvas.width);
    traFolder.add(objects.border.position, 'y', 0, gl.canvas.height);

    const traPivotFolder = gui.addFolder('Pivot Translation');
    traPivotFolder.add(objects.pivot.position, 'x', 0, gl.canvas.width);
    traPivotFolder.add(objects.pivot.position, 'y', 0, gl.canvas.height);

    const rotFolder = gui.addFolder('Rotation');
    rotFolder.add(objects.border.rotRad, 'z', -Math.PI * 2, Math.PI * 2).name('z');

    const scaFolder = gui.addFolder('Scale');
    scaFolder.add(objects.border.scale, 'x', -5, 5);
    scaFolder.add(objects.border.scale, 'y', -5, 5);

    const colFolder = gui.addFolder('Face Colors');
    colFolder.addColor(objects.border, 'color').name('Border and eyes color').onChange((value) => {
        objects.right_eye.color = value;
        objects.left_eye.color = value;
    })
    colFolder.addColor(objects.face, 'color').name('Face color');
    colFolder.addColor(objects.mouth, 'color').name('Mouth color');

}

main()

