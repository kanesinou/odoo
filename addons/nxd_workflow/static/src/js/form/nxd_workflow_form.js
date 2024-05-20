/** @odoo-module **/

import { registry } from "@web/core/registry";
import { createElement, append, getTag } from "@web/core/utils/xml";
import { formView } from "@web/views/form/form_view";
import { FormRenderer } from "@web/views/form/form_renderer";
import { FormCompiler } from "@web/views/form/form_compiler";
import { useService } from "@web/core/utils/hooks";

export class NxdWorkflowFormRenderer extends FormRenderer {
    setup() {
        this.setupProcessButtons();
        super.setup();
    }

    setupProcessButtons() {
        const parser = new DOMParser();
        const process_buttons_fields = this.props.archInfo.xmlDoc.querySelectorAll(`[name="process_buttons"]`);
        for (const process_buttons_field of process_buttons_fields) {
            let header = process_buttons_field.parentNode;
            const divUtil = document.createElement('div');
            header.appendChild(divUtil)
            const process_buttons_field_name = process_buttons_field.getAttribute('name')
            let process_buttons_data = this.props.record.data[process_buttons_field_name];
            process_buttons_data = process_buttons_data.replace(
                /&lt;|&gt;/g, function(s) { return s === "&lt;" ? "<" : ">" }
            );
            if (process_buttons_data != '') {
                divUtil.appendChild(
                    parser.parseFromString(process_buttons_data, "text/xml").documentElement
                );
            }
            const process_state_field = this.props.archInfo.xmlDoc.querySelectorAll(`[name="state"]`);
            let wrapper = divUtil
            while (wrapper.firstChild !== null && wrapper.firstChild.tagName !== 'button') {
                wrapper = wrapper.firstChild
            }
            if (typeof(process_state_field) != 'undefined') {
                for (let child of wrapper.childNodes) {
                    header.insertBefore(child, process_state_field.documentElement);
                }
            } else {
                for (let child of wrapper.childNodes) {
                    header.append(child);
                }
            }
            header.removeChild(process_buttons_field);
            header.removeChild(divUtil)
        }
    }
}

/*export class NxdWorkflowFormCompiler extends FormCompiler {

    compileHeader(el, params) {
        const process_buttons_fields = el.querySelectorAll(`[name="process_buttons"]`);
        for (const process_buttons_field of process_buttons_fields) {
            const compiled_process_buttons_field = this.compileNode(process_buttons_field, params);
            const field_name = compiled_process_buttons_field.getAttribute('name')
        }
        return super.compileHeader(el, params)
    }
}*/

export const NxdWorkflowFormView = {
    ...formView,
    Renderer: NxdWorkflowFormRenderer,
    /*Compiler: NxdWorkflowFormCompiler,*/
};

registry.category("views").add("nxd_workflow_form", NxdWorkflowFormView);