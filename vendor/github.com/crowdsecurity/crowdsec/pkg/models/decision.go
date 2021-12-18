// Code generated by go-swagger; DO NOT EDIT.

package models

// This file was generated by the swagger tool.
// Editing this file might prove futile when you re-run the swagger generate command

import (
	"github.com/go-openapi/errors"
	"github.com/go-openapi/strfmt"
	"github.com/go-openapi/swag"
	"github.com/go-openapi/validate"
)

// Decision Decision
//
// swagger:model Decision
type Decision struct {

	// duration
	// Required: true
	Duration *string `json:"duration"`

	// (only relevant for GET ops) the unique id
	// Read Only: true
	ID int64 `json:"id,omitempty"`

	// the origin of the decision : cscli, crowdsec
	// Required: true
	Origin *string `json:"origin"`

	// scenario
	// Required: true
	Scenario *string `json:"scenario"`

	// the scope of decision : does it apply to an IP, a range, a username, etc
	// Required: true
	Scope *string `json:"scope"`

	// true if the decision result from a scenario in simulation mode
	// Read Only: true
	Simulated *bool `json:"simulated,omitempty"`

	// the type of decision, might be 'ban', 'captcha' or something custom. Ignored when watcher (cscli/crowdsec) is pushing to APIL.
	// Required: true
	Type *string `json:"type"`

	// the value of the decision scope : an IP, a range, a username, etc
	// Required: true
	Value *string `json:"value"`
}

// Validate validates this decision
func (m *Decision) Validate(formats strfmt.Registry) error {
	var res []error

	if err := m.validateDuration(formats); err != nil {
		res = append(res, err)
	}

	if err := m.validateOrigin(formats); err != nil {
		res = append(res, err)
	}

	if err := m.validateScenario(formats); err != nil {
		res = append(res, err)
	}

	if err := m.validateScope(formats); err != nil {
		res = append(res, err)
	}

	if err := m.validateType(formats); err != nil {
		res = append(res, err)
	}

	if err := m.validateValue(formats); err != nil {
		res = append(res, err)
	}

	if len(res) > 0 {
		return errors.CompositeValidationError(res...)
	}
	return nil
}

func (m *Decision) validateDuration(formats strfmt.Registry) error {

	if err := validate.Required("duration", "body", m.Duration); err != nil {
		return err
	}

	return nil
}

func (m *Decision) validateOrigin(formats strfmt.Registry) error {

	if err := validate.Required("origin", "body", m.Origin); err != nil {
		return err
	}

	return nil
}

func (m *Decision) validateScenario(formats strfmt.Registry) error {

	if err := validate.Required("scenario", "body", m.Scenario); err != nil {
		return err
	}

	return nil
}

func (m *Decision) validateScope(formats strfmt.Registry) error {

	if err := validate.Required("scope", "body", m.Scope); err != nil {
		return err
	}

	return nil
}

func (m *Decision) validateType(formats strfmt.Registry) error {

	if err := validate.Required("type", "body", m.Type); err != nil {
		return err
	}

	return nil
}

func (m *Decision) validateValue(formats strfmt.Registry) error {

	if err := validate.Required("value", "body", m.Value); err != nil {
		return err
	}

	return nil
}

// MarshalBinary interface implementation
func (m *Decision) MarshalBinary() ([]byte, error) {
	if m == nil {
		return nil, nil
	}
	return swag.WriteJSON(m)
}

// UnmarshalBinary interface implementation
func (m *Decision) UnmarshalBinary(b []byte) error {
	var res Decision
	if err := swag.ReadJSON(b, &res); err != nil {
		return err
	}
	*m = res
	return nil
}
