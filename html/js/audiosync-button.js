import {qs, ce, createRipple, hexToRgba, convertToHex, getCSSVariableValue, getContrastColor, parseCSS, objectToCSS} from './helpers.js';

class AudioSyncButton extends HTMLElement {
  static get observedAttributes() {
    return ['color', 'disabled', 'noshadow'];
  }
  constructor() {
    super();
    this.attachShadow({mode: 'open'});

    // color higherarchy 
    // color attribute > css '--pop-color' variable > white
    const COLOR = convertToHex(this.getAttribute('color') || getCSSVariableValue('--pop-color') || 'var(--main-color)');
    
    // contrasting text color 
    const CONTRAST_COLOR = getContrastColor(COLOR);

    const CSS_OBJECT = {
      '.button': {
        display: 'inline-flex',
        'min-width': '5.14em',
        margin: '0.29em 0.29em',
        color: CONTRAST_COLOR,
        'background-color': COLOR,
        'text-align': 'center',
        'text-transform': 'uppercase',
        'outline-width': 0,
        'border-radius': '3px',
        padding: '0.7em 0.57em',
        cursor: 'pointer',
        position: 'relative',
        'box-sizing': 'border-box',
        'box-shadow': '0 2px 2px 0 rgba(0,0,0,0.14),0 1px 5px 0 rgba(0,0,0,0.12),0 3px 1px -2px rgba(0,0,0,0.2)',
        '-webkit-user-select': 'none',
        'user-select': 'none',
        'pointer-events': 'all',
        'justify-content': 'center',
        'align-items': 'center',
        transition: 'var(--button-bg-animation)',
        overflow: 'hidden',
        transform: 'translate3d(0, 0, 0)'
      },
      '.button:after': {
        display: 'inline-block',
        'z-index': -1,
        width: '100%',
        height: '100%',
        opacity: 0,
        'border-radius': '3px',
        transition: 'opacity 150ms cubic-bezier(.33,.17,.85,1.1)',
        'box-shadow': '0 8px 10px 1px rgba(0,0,0,.14), 0 3px 14px 2px rgba(0,0,0,.12), 0 5px 5px -3px rgba(0,0,0,.4)',
        content: '" "',
        position: 'absolute',
        top: 0,
        left: 0
      },
      '.button:hover:after': {
        opacity: 1
      },
      '.button:hover:active:after': {
        opacity: 0
      },
      '.button[disabled]': {
        background: 'rgba(84, 84, 84, 0.4)',
        color: '#ffffff',
        'box-shadow': 'none',
        cursor: 'none',
        'pointer-events': 'none'
      },
      '.button[disabled]:active, .button[disabled]:hover, .button[disabled]:active:hover': {
        'box-shadow': 'none',
        'background-color': 'rgba(0, 0, 0, 0.178)'
      },
      '.button[noshadow], .button[noshadow]:hover, .button[noshadow]:hover:after, .button[noshadow]:after': {
        'box-shadow': 'none'
      },
      '.button[noshadow]:active': {
        'box-shadow': '0 2px 2px 0 rgba(0,0,0,0.14),0 1px 5px 0 rgba(0,0,0,0.12),0 3px 1px -2px rgba(0,0,0,0.2)'
      },
      '.button > *': {
        'pointer-events': 'none'
      },
      '@keyframes ripple-animation': {
        to: {
          transform: 'scale(4)',
          opacity: 0
        }
      },
      '.ripple-effect': {
        position: 'absolute',
        'border-radius': '50%',
        background: hexToRgba(CONTRAST_COLOR),
        animation: 'ripple-animation 0.7s linear'
      }
    };

    const ELEMENT_STYLES = ce('style');
    ELEMENT_STYLES.textContent = objectToCSS(CSS_OBJECT);

    this.button = ce('div');
    this.button.classList.add('button');
    this.button.appendChild(ce('slot'));
    
    [
      ELEMENT_STYLES,
      this.button
    ].forEach(el => this.shadowRoot.appendChild(el));
  }

  /**
   * element connected to DOM
   */
  connectedCallback() {
    if (this.hasAttribute('disabled')) {
      this.button.setAttribute('disabled', Number(this.getAttribute('disabled')));
    }
    if (this.hasAttribute('noshadow')) {
      this.button.setAttribute('noshadow', Number(this.getAttribute('noshadow')));
    }
    this.button.addEventListener('click', e => {
      // no ripple for disabled button
      if (this.button.hasAttribute('disabled')) return;
      createRipple(e) 
    });

    /**
     * attach styles for the button's nested elements
     */

    // defaults to 'document'
    let STYLE_NODE = qs('style');

    // for <music-library> initial scan
    if (qs('style', this.parentNode.parentNode.parentNode)) {
      STYLE_NODE = qs('style', this.parentNode.parentNode.parentNode);
    }

    // for <sync-ui> 
    if (qs('style', this.parentNode.parentNode)) {
      STYLE_NODE = qs('style', this.parentNode.parentNode);
    }

    // capture styles
    const CSS_STYLES = parseCSS(STYLE_NODE.textContent);

    // css properties
    CSS_STYLES['audiosync-button > div'] = {
      display: 'flex',
      'flex-direction': 'row'
    };
    CSS_STYLES['audiosync-button > div > :first-child'] = {
      'margin-right': '16px'
    };
    CSS_STYLES['audiosync-button > div > :nth-child(2)'] = {
      display: 'flex',
      'align-items': 'center',
      'margin-right':'16px'
    };
    
    //  apply new css
    STYLE_NODE.textContent = objectToCSS(CSS_STYLES);
  }

  /**
   * add's an click event listener
   * 
   * @param {Function} cb callback function
   */
  onClick(cb) {
    this.button.addEventListener('click', e => {
      if (this.hasAttribute('disabled')) return;
      cb(e);
    });
  }

  /**
   * attribute has changed 
   * 
   * @param {String} name
   * @param {Number} oldVal
   * @param {Number} newVal
   */
  attributeChangedCallback(name, oldVal, newVal) {
    if (name === 'color') {
      if (newVal === null) return;
      
      // capture current styles and remove .new-color and .ripple-effect classes
      const ELEMENT_STYLES = parseCSS(qs('style', this.shadowRoot).textContent);
      
      // background-color in hex format
      const COLOR = convertToHex(newVal);
      
      // text / ripple color
      const CONTRAST_COLOR = getContrastColor(COLOR);
      
      // create the new style 
      ELEMENT_STYLES['.new-color'] = {
        'background-color': COLOR,
        color: CONTRAST_COLOR
      };
      ELEMENT_STYLES['.ripple-effect'].background = hexToRgba(CONTRAST_COLOR);
      
      // update styles
      qs('style', this.shadowRoot).textContent = objectToCSS(ELEMENT_STYLES);         
      
      // set the new class
      this.button.classList.add('new-color');

    } else if (['disabled','noshadow'].includes(name)) {
      // reflect attribute changes to the button element
      if (this.hasAttribute(name)) {
        this.button.setAttribute(name, '');
      } else {
        this.button.removeAttribute(name);
      }
    }
  }
}
customElements.define('audiosync-button', AudioSyncButton);
