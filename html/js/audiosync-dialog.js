import {fadeIn, fadeOut, animateElement, objectToCSS} from './helpers.js';

/**
 * dialog box 
 */
class AudioSyncDialog extends HTMLElement {
  static get observedAttributes() {
    return ['small'];
  }
  constructor() {
    super();
    const cssObj = {
      "#click-blocker": {
        "position": "absolute",
        "top": 0,
        "bottom": 0,
        "left": 0,
        "right": 0,
        "background-color": "rgba(0, 0, 0, 0.4)",
        "pointer-events": "all",
        "z-index": 3
      },
      ".allow-clicks": {
        "pointer-events": "none",
        "display": "none"
      },
      ".dialog": {
        "position": "absolute",
        "top": "150px",
        "bottom": "150px",
        "left": "25px",
        "right": "25px",
        "color": "#333333",
        "padding": "24px",
        "background": "#ffffff",
        "border-radius": "3px",
        "box-shadow": "0 2px 2px 0 rgba(0,0,0,0.14),0 1px 5px 0 rgba(0,0,0,0.12),0 3px 1px -2px rgba(0,0,0,0.2)",
        "text-align": "center",
        "z-index": 4,
        "transform": "scale3d(0, 0, 0)",
        "max-width": "650px"
      },
      ".small": {
        "top": "300px",
        "bottom": "300px",
        "left": "100px",
        "right": "100px"
      }
    };

    const sheet = document.createElement('style');
    sheet.textContent = objectToCSS(cssObj);

    this.blocker = document.createElement('div');
    this.blocker.id = 'click-blocker';
    this.blocker.classList.add('allow-clicks');

    this.dialog = document.createElement('div');
    this.dialog.classList.add('dialog');
    this.dialog.appendChild(document.createElement('slot'));
    
    const shadow = this.attachShadow({mode: "open"});
    [
      sheet,
      this.blocker,
      this.dialog
    ].forEach(el => shadow.appendChild(el));
  }

  /**
   * element connected to DOM
   */
  connectedCallback() {
    this.hasAttribute('small') ? this.dialog.classList.add('small') : this.dialog.classList.remove('small');
    this.setAttribute('opened', 0);
  }

  /**
   * open the dialog
   */
  async open() {
    fadeIn(this.blocker);
    this.blocker.classList.remove('allow-clicks');
    await animateElement(this.dialog, 'scale3d(1, 1, 1)', 250);
    this.setAttribute('opened', 1);
  }

  /**
   * close the dialog
   */
  async close() {
    fadeOut(this.blocker);
    await animateElement(this.dialog, 'scale3d(0, 0, 0)', 250);
    this.blocker.classList.add('allow-clicks');
    this.setAttribute('opened', 0);
  }

  /**
   * attribute has changed 
   * 
   * @param {String} name
   * @param {Number} oldVal
   * @param {Number} newVal
   */
  attributeChangedCallback(name, oldVal, newVal) {
    this.hasAttribute('small') ? this.dialog.classList.add('small') : this.dialog.classList.remove('small');
  }
}
customElements.define('audiosync-dialog', AudioSyncDialog);
